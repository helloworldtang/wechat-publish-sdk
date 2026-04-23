"""SDK 异常类定义"""


class WeChatPublishError(Exception):
    """基础异常类"""
    pass


class SignatureError(WeChatPublishError):
    """签名验证失败"""
    pass


class AuthenticationError(WeChatPublishError):
    """认证失败"""
    pass


class AccountNotFoundError(WeChatPublishError):
    """账号不存在"""
    pass


class PublishFailedError(WeChatPublishError):
    """发布失败"""
    pass


class UploadError(WeChatPublishError):
    """上传失败"""
    pass


class ValidationError(WeChatPublishError):
    """参数验证失败"""
    pass
