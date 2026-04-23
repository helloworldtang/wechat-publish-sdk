"""WeChat Publish SDK

微信公众号发布服务的 Python SDK，封装了所有 API 操作。

使用示例:
    >>> from wechat_publish_sdk import WeChatClient, PublishRequest
    >>>
    >>> client = WeChatClient(
    ...     base_url="http://localhost:3000",
    ...     signing_key="your_signing_key_in_hex",
    ...     default_account="mingdeng"
    ... )
    >>>
    >>> result = client.publish_article(
    ...     PublishRequest(
    ...         title="测试标题",
    ...         content="# 测试内容"
    ...     )
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

__version__ = "1.0.0"
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
    "WeChatPublishError",
    "SignatureError",
    "AuthenticationError",
    "AccountNotFoundError",
    "PublishFailedError",
    "UploadError",
    "ValidationError",
]
