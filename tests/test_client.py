"""单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from wechat_publish_sdk import WeChatClient, PublishRequest, ValidationError
from wechat_publish_sdk.exceptions import AccountNotFoundError
from wechat_publish_sdk.oidc import OIDCConfig


BASE_URL = "https://yyps.net"


class TestWeChatClient:
    """客户端测试"""

    def test_init_with_api_key(self):
        """API Key 初始化"""
        client = WeChatClient(base_url=BASE_URL, api_key="sk_live_test")
        assert client.base_url == BASE_URL
        assert client.api_version == "v1"
        assert client.endpoint_base == f"{BASE_URL}/api/v1/mp"
        assert client.api_key == "sk_live_test"
        assert client._oidc_client is None

    def test_init_with_oidc(self):
        """OIDC 初始化"""
        cfg = OIDCConfig(client_id="cid", client_secret="sec")
        client = WeChatClient(base_url=BASE_URL, oidc=cfg)
        assert client._oidc_client is not None
        assert client.api_key is None

    def test_init_with_custom_version(self):
        """自定义 API 版本"""
        client = WeChatClient(
            base_url=BASE_URL, api_key="sk_live_test", api_version="dev"
        )
        assert client.api_version == "dev"
        assert client.endpoint_base == f"{BASE_URL}/api/dev/mp"

    def test_init_no_version_prefix(self):
        """空 api_version 使用无版本前缀路径"""
        client = WeChatClient(
            base_url=BASE_URL, api_key="sk_live_test", api_version=""
        )
        assert client.endpoint_base == f"{BASE_URL}/api/mp"

    def test_init_no_auth_raises(self):
        """未提供任何认证方式应抛 ValidationError"""
        with pytest.raises(ValidationError):
            WeChatClient(base_url=BASE_URL)

    def test_init_signing_key_deprecated(self):
        """signing_key 触发 DeprecationWarning（仍接受，向后兼容）"""
        with pytest.warns(DeprecationWarning):
            client = WeChatClient(base_url=BASE_URL, signing_key="a" * 64)
        assert client.signing_key == "a" * 64

    def test_get_account_with_default(self):
        """使用默认账号"""
        client = WeChatClient(
            base_url=BASE_URL, api_key="k", default_account="default_account"
        )
        assert client._get_account() == "default_account"

    def test_get_account_without_default_raises(self):
        """无默认账号且不传 account 抛异常"""
        client = WeChatClient(base_url=BASE_URL, api_key="k")
        with pytest.raises(ValidationError):
            client._get_account()

    def test_get_account_explicit(self):
        """显式指定账号优先于默认账号"""
        client = WeChatClient(
            base_url=BASE_URL, api_key="k", default_account="default"
        )
        assert client._get_account("explicit_account") == "explicit_account"

    def test_build_auth_headers_api_key(self):
        """API Key 模式生成 X-API-Key 头"""
        client = WeChatClient(base_url=BASE_URL, api_key="sk_live_x")
        assert client._build_auth_headers() == {"X-API-Key": "sk_live_x"}

    def test_build_auth_headers_oidc(self):
        """OIDC 模式生成 Authorization: Bearer 头"""
        cfg = OIDCConfig(
            client_id="cid", client_secret="sec",
            token_endpoint="https://auth.ai-as.cc/token",
        )
        client = WeChatClient(base_url=BASE_URL, oidc=cfg)
        client._oidc_client.get_valid_token = MagicMock(return_value="token123")
        assert client._build_auth_headers() == {"Authorization": "Bearer token123"}

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_success_with_api_key_header(self, mock_post):
        """发布成功且请求携带 X-API-Key 头"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "发布成功", "draft_id": "draft_123"},
        )
        client = WeChatClient(
            base_url=BASE_URL, api_key="sk_live_test", default_account="test_account"
        )

        result = client.publish_article(
            PublishRequest(title="测试标题", content="# 测试内容")
        )

        assert result.success is True
        assert result.draft_id == "draft_123"
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-API-Key"] == "sk_live_test"

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_with_cover(self, mock_post):
        """cover=ai 时 cover + cover_image_prompt 进 payload"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "ok", "draft_id": "d_cover"},
        )
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="t")
        client.publish_article(
            PublishRequest(
                title="t", content="c", cover="ai", cover_image_prompt="极简几何封面"
            )
        )
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["cover"] == "ai"
        assert payload["cover_image_prompt"] == "极简几何封面"

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_with_oidc_bearer_header(self, mock_post):
        """OIDC 模式发布，请求携带 Authorization: Bearer"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "ok", "draft_id": "d1"},
        )
        cfg = OIDCConfig(
            client_id="cid", client_secret="sec",
            token_endpoint="https://auth.ai-as.cc/token",
        )
        client = WeChatClient(
            base_url=BASE_URL, oidc=cfg, default_account="test_account"
        )
        # 避免 OIDC 客户端发起真实 HTTP discovery/token 请求
        client._oidc_client.get_valid_token = MagicMock(return_value="abc")

        client.publish_article(PublishRequest(title="t", content="c"))

        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer abc"

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_404(self, mock_post):
        """发布 404 抛 AccountNotFoundError"""
        mock_post.return_value = Mock(
            status_code=404,
            json=lambda: {"success": False, "message": "接口不存在"},
        )
        client = WeChatClient(
            base_url=BASE_URL, api_key="k", default_account="t"
        )
        with pytest.raises(AccountNotFoundError):
            client.publish_article(PublishRequest(title="测试", content="内容"))

    def test_publish_article_validation_error(self):
        """空 title / 空 content 抛 ValidationError"""
        client = WeChatClient(base_url=BASE_URL, api_key="k")
        with pytest.raises(ValidationError):
            client.publish_article(PublishRequest(title="", content="内容"))
        with pytest.raises(ValidationError):
            client.publish_article(PublishRequest(title="标题", content=""))

    @patch("wechat_publish_sdk.client.os.path.exists")
    def test_upload_image_file_not_found(self, mock_exists):
        """文件不存在抛 ValidationError"""
        mock_exists.return_value = False
        client = WeChatClient(base_url=BASE_URL, api_key="k")

        from wechat_publish_sdk import UploadRequest
        with pytest.raises(ValidationError):
            client.upload_image(
                UploadRequest(account="test", file_path="/nonexistent/file.jpg")
            )
