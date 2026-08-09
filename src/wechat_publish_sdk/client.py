"""WeChat Publish 服务的同步 HTTP 客户端。"""

import os
import secrets
import time
import warnings
from typing import Any, Dict, Optional

import requests

from .exceptions import AccountNotFoundError, ValidationError, WeChatPublishError
from .models import (
    MaterialsListResult,
    PublishRequest,
    PublishResult,
    RenderRequest,
    RenderResult,
    UploadRequest,
    UploadResult,
)
from .oidc import OIDCConfig, OIDCClient


class WeChatClient:
    """微信发布服务客户端

    封装了所有与后端服务的交互，包括认证、错误处理等。

    认证方式（三选一，互斥）:
        - ``api_key``: ``X-API-Key`` 头（推荐，对接 ai-as.cc ``/api/keys/validate``）
        - ``oidc``: ``Authorization: Bearer`` 头
          （OIDC ``client_credentials``，对接 auth.ai-as.cc）
        - ``signing_key``: 旧版 HMAC 签名
          （已废弃，仅为兼容保留，service 已不校验）
    """

    def __init__(
        self,
        base_url: str,
        signing_key: Optional[str] = None,
        api_key: Optional[str] = None,
        oidc: Optional[OIDCConfig] = None,
        default_account: Optional[str] = None,
        api_version: str = "v1",
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """初始化客户端

        Args:
            base_url: 后端服务地址，如 https://yyps.net
            signing_key: HMAC 签名密钥（已废弃，建议改用 api_key 或 oidc）
            api_key: API Key（推荐，对应 X-API-Key 头）
            oidc: OIDC 配置（OIDCConfig，对应 Authorization: Bearer 头）
            default_account: 默认账号，所有请求可省略 account 参数
            api_version: API 版本，默认 "v1"；传 "" 或 "default" 使用无版本前缀路径
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = base_url.rstrip("/")
        self.default_account = default_account
        self.api_version = api_version
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_ssl
        # 禁用自动代理检测，避免连接到错误的代理
        self.session.trust_env = False

        # 认证方式初始化（三选一，互斥）
        self.api_key: Optional[str] = None
        self.signing_key: Optional[str] = None
        self._oidc_client: Optional[OIDCClient] = None

        if oidc is not None:
            self._oidc_client = OIDCClient(oidc, session=self.session, timeout=timeout)
        elif api_key:
            self.api_key = api_key
        elif signing_key:
            warnings.warn(
                "signing_key 已废弃：service 侧不再校验 HMAC 签名，"
                "请改用 api_key 或 oidc 认证。",
                DeprecationWarning,
                stacklevel=2,
            )
            self.signing_key = signing_key  # 仅留存，不再用于生成签名
        else:
            raise ValidationError("必须提供 api_key、oidc 或 signing_key 之一")

        # 构建端点基础路径
        # 支持无版本前缀的路径（api_version="" 或 None）以适配后端规范
        if api_version and api_version not in ("", "default"):
            self.endpoint_base = f"{self.base_url}/api/{api_version}/mp"
        else:
            self.endpoint_base = f"{self.base_url}/api/mp"

    def _build_auth_headers(self) -> Dict[str, str]:
        """根据当前认证方式构建请求头"""
        if self._oidc_client is not None:
            token = self._oidc_client.get_valid_token()
            return {"Authorization": f"Bearer {token}"}
        if self.api_key:
            return {"X-API-Key": self.api_key}
        # signing_key 模式：service 已不校验签名，不附加认证头
        return {}

    def _get_account(self, account: Optional[str] = None) -> str:
        """获取账号标识，使用默认账号"""
        if not account:  # 处理 None 和空字符串
            if self.default_account is None:
                raise ValidationError("未指定 account，且未设置 default_account")
            return self.default_account
        return account

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应，统一错误处理

        Args:
            response: requests.Response 对象

        Returns:
            解析后的 JSON 数据

        Raises:
            WeChatPublishError: 根据响应内容抛出相应的异常
        """
        try:
            data = response.json()
        except ValueError as error:
            # 服务返回了非 JSON 响应（如 HTML 错误页面）
            if response.status_code == 404:
                raise AccountNotFoundError("接口不存在或路径错误") from error
            if response.status_code == 422:
                raise ValidationError(f"参数格式错误: {response.text[:100]}") from error
            if response.status_code >= 500:
                raise WeChatPublishError(f"服务器错误: {response.text[:100]}") from error
            raise WeChatPublishError(f"响应解析失败: {response.text[:100]}") from error

        if response.status_code == 404:
            raise AccountNotFoundError(data.get("message", "接口不存在"))

        if response.status_code in (401, 403):
            raise WeChatPublishError(
                f"认证失败 ({response.status_code}): {data.get('message', response.text)}"
            )

        if response.status_code >= 500:
            raise WeChatPublishError(f"服务器错误: {data.get('message', response.text)}")

        if not data.get("success", False):
            msg = data.get("message", "未知错误")
            error_code = data.get("error_code")
            raise WeChatPublishError(f"{msg} (错误码: {error_code})")

        return data

    def _build_publish_payload(self, request: PublishRequest, account: str) -> Dict[str, Any]:
        """构建发布请求体，仅包含调用方显式启用的可选字段。"""
        timestamp = int(time.time())
        payload: Dict[str, Any] = {
            "account": account,
            "title": request.title,
            "content": request.content,
            "timestamp": timestamp,
            "nonce": secrets.token_hex(16),
            "expires_at": timestamp + 300,
        }
        optional_fields = {
            "thumb_media_id": request.thumb_media_id,
            "content_format": request.content_format,
            "theme": request.theme,
            "author": request.author,
            "digest": request.digest,
            "show_cover_pic": request.show_cover_pic,
            "need_open_comment": request.need_open_comment,
            "only_fans_can_comment": request.only_fans_can_comment,
            "cover": request.cover,
            "cover_image_prompt": request.cover_image_prompt,
            "idempotency_key": request.idempotency_key,
        }
        populated_fields = {
            key: value
            for key, value in optional_fields.items()
            if value is not None and value != ""
        }
        payload.update(populated_fields)
        if request.force_publish:
            payload["force_publish"] = True
        return payload

    def publish_article(self, request: PublishRequest) -> PublishResult:
        """发布文章到微信公众号草稿箱

        Args:
            request: 发布请求对象

        Returns:
            发布结果，包含 draft_id

        Raises:
            ValidationError: 参数验证失败
            PublishFailedError: 发布失败
        """
        # 验证必填参数
        if not request.title or not request.content:
            raise ValidationError("title 和 content 不能为空")

        account = self._get_account(request.account)
        payload = self._build_publish_payload(request, account)

        url = f"{self.endpoint_base}/publish"
        response = self.session.post(
            url,
            json=payload,
            headers=self._build_auth_headers(),
            timeout=self.timeout,
        )

        data = self._handle_response(response)

        return PublishResult(
            success=data.get("success", False),
            message=data.get("message", ""),
            draft_id=data.get("draft_id"),
            error_code=data.get("error_code"),
            duplicate=data.get("duplicate", False),
            duplicate_of=data.get("duplicate_of"),
            duplicate_status=data.get("duplicate_status"),
        )

    def upload_image(self, request: UploadRequest) -> UploadResult:
        """上传图片素材

        Args:
            request: 上传请求对象

        Returns:
            上传结果，包含 media_id 和 url

        Raises:
            ValidationError: 文件不存在
            UploadError: 上传失败
        """
        # 验证文件存在
        if not os.path.exists(request.file_path):
            raise ValidationError(f"文件不存在: {request.file_path}")

        account = self._get_account(request.account)
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        expires_at = timestamp + 300

        # 构建请求数据
        data = {
            "account": account,
            "timestamp": str(timestamp),
            "nonce": nonce,
            "expires_at": str(expires_at),
        }

        # 发送 multipart/form-data 请求
        url = f"{self.endpoint_base}/materials/upload"
        with open(request.file_path, "rb") as f:
            files = {"file": f}

            response = self.session.post(
                url,
                files=files,
                data=data,
                headers=self._build_auth_headers(),
                timeout=self.timeout,
            )

        resp_data = self._handle_response(response)

        return UploadResult(
            success=resp_data.get("success", False),
            message=resp_data.get("message", ""),
            media_id=resp_data.get("media_id"),
            url=resp_data.get("url"),
            error_code=resp_data.get("error_code"),
        )

    def list_materials(
        self,
        account: Optional[str] = None,
        material_type: str = "image",
        offset: int = 0,
        count: int = 20,
    ) -> MaterialsListResult:
        """查询素材列表

        Args:
            account: 账号标识
            material_type: 素材类型，默认 "image"
            offset: 偏移量，默认 0
            count: 数量，默认 20（最大 20）

        Returns:
            素材列表结果
        """
        account = self._get_account(account)

        url = f"{self.endpoint_base}/materials/list"
        payload = {
            "account": account,
            "material_type": material_type,
            "timestamp": int(time.time()),
            "offset": offset,
            "count": min(count, 20),
        }

        response = self.session.post(
            url,
            json=payload,
            headers=self._build_auth_headers(),
            timeout=self.timeout,
        )

        data = self._handle_response(response)

        return MaterialsListResult(
            success=data.get("success", False),
            message=data.get("message", ""),
            total_count=data.get("total_count", 0),
            item_count=data.get("item_count", 0),
            items=data.get("items", []),
            error_code=data.get("error_code"),
        )

    def render_markdown(self, request: RenderRequest) -> RenderResult:
        """渲染 Markdown 为微信兼容 HTML

        Args:
            request: 渲染请求对象

        Returns:
            渲染结果，包含 HTML 内容
        """
        url = f"{self.endpoint_base}/render/markdown"
        payload = {"content": request.content, "theme": request.theme}

        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout,
        )

        data = self._handle_response(response)

        return RenderResult(
            success=data.get("success", False),
            html=data.get("html", ""),
            message=data.get("message", ""),
            error_code=data.get("error_code"),
        )

    def render_html(self, content: str, theme: str = "default") -> RenderResult:
        """优化 HTML 为微信兼容格式

        Args:
            content: HTML 内容
            theme: 主题名称

        Returns:
            渲染结果
        """
        url = f"{self.endpoint_base}/render/html"
        payload = {"content": content, "theme": theme}

        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout,
        )

        data = self._handle_response(response)

        return RenderResult(
            success=data.get("success", False),
            html=data.get("html", ""),
            message=data.get("message", ""),
            error_code=data.get("error_code"),
        )
