"""单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from wechat_publish_sdk import WeChatClient, PublishRequest, ValidationError
from wechat_publish_sdk.exceptions import AccountNotFoundError


class TestWeChatClient:
    """客户端测试"""

    def test_init(self):
        """测试客户端初始化"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64  # 64 hex chars = 32 bytes
        )
        assert client.base_url == "http://localhost:3000"
        assert client.api_version == "v1"
        assert client.endpoint_base == "http://localhost:3000/api/v1/mp"

    def test_init_with_custom_version(self):
        """测试自定义版本"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64,
            api_version="dev"
        )
        assert client.api_version == "dev"
        assert client.endpoint_base == "http://localhost:3000/api/dev/mp"

    def test_make_signature(self):
        """测试签名生成"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64
        )
        sig = client._make_signature("test_account", 1234567890, "body_hash_value")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 hex = 64 chars

    def test_get_account_with_default(self):
        """测试使用默认账号"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64,
            default_account="default_account"
        )
        account = client._get_account()
        assert account == "default_account"

    def test_get_account_without_default_raises(self):
        """测试无默认账号且不传 account 时抛异常"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64
        )
        with pytest.raises(ValidationError):
            client._get_account()

    def test_get_account_explicit(self):
        """测试显式指定账号"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64,
            default_account="default"
        )
        account = client._get_account("explicit_account")
        assert account == "explicit_account"

    @patch('wechat_publish_sdk.client.requests.Session.post')
    def test_publish_article_success(self, mock_post):
        """测试发布文章成功"""
        mock_post.return_value = Mock(
            json=lambda: {"success": True, "message": "发布成功", "draft_id": "draft_123"}
        )

        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64,
            default_account="test_account"
        )

        result = client.publish_article(
            PublishRequest(
                title="测试标题",
                content="# 测试内容"
            )
        )

        assert result.success is True
        assert result.draft_id == "draft_123"
        assert mock_post.called

    @patch('wechat_publish_sdk.client.requests.Session.post')
    def test_publish_article_404(self, mock_post):
        """测试发布文章 404"""
        mock_post.return_value = Mock(
            status_code=404,
            json=lambda: {"success": False, "message": "接口不存在"}
        )

        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64,
            default_account="test_account"
        )

        with pytest.raises(AccountNotFoundError):
            client.publish_article(
                PublishRequest(
                    title="测试",
                    content="内容"
                )
            )

    def test_publish_article_validation_error(self):
        """测试参数验证失败"""
        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64
        )

        with pytest.raises(ValidationError):
            client.publish_article(
                PublishRequest(
                    title="",  # 空标题
                    content="内容"
                )
            )

        with pytest.raises(ValidationError):
            client.publish_article(
                PublishRequest(
                    title="标题",
                    content=""  # 空内容
                )
            )

    @patch('wechat_publish_sdk.client.os.path.exists')
    def test_upload_image_file_not_found(self, mock_exists):
        """测试文件不存在"""
        mock_exists.return_value = False

        client = WeChatClient(
            base_url="http://localhost:3000",
            signing_key="a" * 64
        )

        from wechat_publish_sdk import UploadRequest
        with pytest.raises(ValidationError):
            client.upload_image(
                UploadRequest(
                    account="test",
                    file_path="/nonexistent/file.jpg"
                )
            )
