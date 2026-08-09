"""WeChatClient 回归测试。"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from wechat_publish_sdk import (
    PublishRequest,
    ValidationError,
    WeChatClient,
    WeChatPublishError,
)
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
            client_id="cid",
            client_secret="sec",
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
    def test_publish_article_default_payload_is_backward_compatible(self, mock_post):
        """默认请求体保留原字段且不发送未启用的判重选项。"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "ok", "draft_id": "d1"},
        )
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="account-a")

        client.publish_article(PublishRequest(title="title", content="content"))

        payload = mock_post.call_args.kwargs["json"]
        assert payload["account"] == "account-a"
        assert payload["content_format"] == "markdown"
        assert payload["show_cover_pic"] == 1
        assert payload["need_open_comment"] == 1
        assert payload["only_fans_can_comment"] == 0
        assert "idempotency_key" not in payload
        assert "force_publish" not in payload

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
    def test_publish_article_with_idempotency_options(self, mock_post):
        """幂等键和强制发布透传到请求体"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "success": True,
                "message": "发布成功",
                "draft_id": "draft_new",
                "duplicate": False,
            },
        )
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="t")

        result = client.publish_article(
            PublishRequest(
                title="t",
                content="c",
                idempotency_key="article-42:revision-3",
                force_publish=True,
            )
        )

        _, kwargs = mock_post.call_args
        assert kwargs["json"]["idempotency_key"] == "article-42:revision-3"
        assert kwargs["json"]["force_publish"] is True
        assert result.duplicate is False

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_duplicate_succeeded(self, mock_post):
        """已成功的重复请求返回原草稿和历史记录"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "success": True,
                "message": "检测到重复内容，已跳过发布，与历史记录 #17 相同",
                "draft_id": "draft_existing",
                "duplicate": True,
                "duplicate_of": 17,
                "duplicate_status": "succeeded",
            },
        )
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="t")

        result = client.publish_article(PublishRequest(title="t", content="c"))

        assert result.success is True
        assert result.draft_id == "draft_existing"
        assert result.duplicate is True
        assert result.duplicate_of == 17
        assert result.duplicate_status == "succeeded"

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_duplicate_processing(self, mock_post):
        """处理中的重复请求保留无草稿 ID 的状态语义"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "success": True,
                "message": "相同内容正在发布中，已跳过重复请求",
                "draft_id": None,
                "duplicate": True,
                "duplicate_status": "processing",
            },
        )
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="t")

        result = client.publish_article(PublishRequest(title="t", content="c"))

        assert result.success is True
        assert result.draft_id is None
        assert result.duplicate is True
        assert result.duplicate_of is None
        assert result.duplicate_status == "processing"

    @patch("wechat_publish_sdk.client.requests.Session.post")
    def test_publish_article_with_oidc_bearer_header(self, mock_post):
        """OIDC 模式发布，请求携带 Authorization: Bearer"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"success": True, "message": "ok", "draft_id": "d1"},
        )
        cfg = OIDCConfig(
            client_id="cid",
            client_secret="sec",
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
        client = WeChatClient(base_url=BASE_URL, api_key="k", default_account="t")
        with pytest.raises(AccountNotFoundError):
            client.publish_article(PublishRequest(title="测试", content="内容"))

    @pytest.mark.parametrize(
        ("status_code", "payload", "expected_message"),
        [
            (401, {"success": False, "message": "token 过期"}, r"认证失败 \(401\)"),
            (500, {"success": False, "message": "database unavailable"}, "服务器错误"),
            (400, {"success": False, "message": "bad request", "error_code": "E400"}, "E400"),
        ],
    )
    def test_handle_json_error_responses(self, status_code, payload, expected_message):
        """JSON 错误响应继续映射为 SDK 基础异常。"""
        client = WeChatClient(base_url=BASE_URL, api_key="k")
        response = Mock(status_code=status_code, text="response body", json=lambda: payload)

        with pytest.raises(WeChatPublishError, match=expected_message):
            client._handle_response(response)

    def test_handle_non_json_validation_error(self):
        """非 JSON 的 422 响应继续映射为参数校验异常。"""
        client = WeChatClient(base_url=BASE_URL, api_key="k")
        response = Mock(status_code=422, text="invalid payload")
        response.json.side_effect = ValueError("not json")

        with pytest.raises(ValidationError, match="参数格式错误"):
            client._handle_response(response)

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
