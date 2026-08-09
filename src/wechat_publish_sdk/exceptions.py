"""WeChat Publish SDK 的公开异常体系。"""


class WeChatPublishError(Exception):
    """SDK 所有异常的基类。"""


class SignatureError(WeChatPublishError):
    """签名验证失败。"""


class AuthenticationError(WeChatPublishError):
    """认证失败。"""


class AccountNotFoundError(WeChatPublishError):
    """账号不存在。"""


class PublishFailedError(WeChatPublishError):
    """发布失败。"""


class UploadError(WeChatPublishError):
    """上传失败。"""


class ValidationError(WeChatPublishError):
    """参数验证失败。"""
