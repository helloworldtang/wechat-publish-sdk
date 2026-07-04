"""WeChat Publish SDK

微信公众号发布服务的 Python SDK，封装了所有 API 操作。

使用示例（API Key 认证，推荐）::

    >>> from wechat_publish_sdk import WeChatClient, PublishRequest
    >>>
    >>> client = WeChatClient(
    ...     base_url="https://yyps.net",
    ...     api_key="sk_live_xxx",
    ...     default_account="mingdeng"
    ... )
    >>>
    >>> result = client.publish_article(
    ...     PublishRequest(title="测试标题", content="# 测试内容")
    ... )

OIDC 认证（可选）::

    >>> from wechat_publish_sdk import WeChatClient, OIDCConfig
    >>> client = WeChatClient(
    ...     base_url="https://yyps.net",
    ...     oidc=OIDCConfig(client_id="...", client_secret="...")
    ... )
"""

from .client import WeChatClient
from .models import (
    PublishRequest,
    PublishResult,
    UploadRequest,
    UploadResult,
    MaterialsListResult,
    MaterialItem,
    RenderRequest,
    RenderResult
)
from .exceptions import (
    WeChatPublishError,
    SignatureError,
    AuthenticationError,
    AccountNotFoundError,
    PublishFailedError,
    UploadError,
    ValidationError
)
from .oidc import OIDCConfig, OIDCClient

__version__ = "1.1.0"

__all__ = [
    "WeChatClient",
    "PublishRequest",
    "PublishResult",
    "UploadRequest",
    "UploadResult",
    "MaterialsListResult",
    "MaterialItem",
    "RenderRequest",
    "RenderResult",
    "OIDCConfig",
    "OIDCClient",
    "WeChatPublishError",
    "SignatureError",
    "AuthenticationError",
    "AccountNotFoundError",
    "PublishFailedError",
    "UploadError",
    "ValidationError",
]
