"""WeChat Client 核心实现"""
import hmac
import hashlib
import time
import os
from typing import Optional, Dict, Any
import requests

from .models import (
    PublishRequest, PublishResult, UploadRequest, UploadResult,
    MaterialsListResult, RenderRequest, RenderResult
)
from .exceptions import (
    WeChatPublishError, SignatureError, AccountNotFoundError,
    PublishFailedError, UploadError, ValidationError
)


class WeChatClient:
    """微信发布服务客户端

    封装了所有与后端服务的交互，包括签名生成、错误处理等。
    """

    def __init__(
        self,
        base_url: str,
        signing_key: str,
        default_account: Optional[str] = None,
        api_version: str = "v1",
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """初始化客户端

        Args:
            base_url: 后端服务地址，如 http://localhost:3000
            signing_key: HMAC 签名密钥（十六进制字符串）
            default_account: 默认账号，所有请求可省略 account 参数
            api_version: API 版本，默认 "v1"
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = base_url.rstrip('/')
        self.signing_key = bytes.fromhex(signing_key)
        self.default_account = default_account
        self.api_version = api_version
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_ssl
        # 禁用自动代理检测，避免连接到错误的代理
        self.session.trust_env = False

        # 构建端点基础路径
        # 支持无版本前缀的路径（api_version="" 或 None）以适配后端规范
        if api_version and api_version not in ("", "default"):
            self.endpoint_base = f"{self.base_url}/api/{api_version}/mp"
        else:
            # 使用标准路径 /api/mp/（符合 API_SPECIFICATION.md）
            self.endpoint_base = f"{self.base_url}/api/mp"

    def _make_signature(self, account: str, timestamp: int, body_hash: str) -> str:
        """生成 HMAC-SHA256 签名

        Args:
            account: 账号标识
            timestamp: Unix 时间戳
            body_hash: 内容 SHA256 哈希

        Returns:
            十六进制签名字符串
        """
        data = f"{account}{timestamp}{body_hash}"
        mac = hmac.new(self.signing_key, data.encode(), hashlib.sha256)
        return mac.hexdigest()

    def _get_account(self, account: Optional[str] = None) -> str:
        """获取账号标识，使用默认账号"""
        if account is None:
            if self.default_account is None:
                raise ValidationError("未指定 account，且未设置 default_account")
            return self.default_account
        return account

    def _handle_response(self, response: requests.Response, success_msg: str = "操作成功") -> Dict[str, Any]:
        """处理响应，统一错误处理

        Args:
            response: requests.Response 对象
            success_msg: 成功时的默认消息

        Returns:
            解析后的 JSON 数据

        Raises:
            WeChatPublishError: 根据响应内容抛出相应的异常
        """
        try:
            data = response.json()
        except ValueError:
            # 服务返回了非 JSON 响应（如 HTML 错误页面）
            if response.status_code == 404:
                raise AccountNotFoundError("接口不存在或路径错误")
            elif response.status_code == 422:
                raise ValidationError(f"参数格式错误: {response.text[:100]}")
            elif response.status_code >= 500:
                raise WeChatPublishError(f"服务器错误: {response.text[:100]}")
            else:
                raise WeChatPublishError(f"响应解析失败: {response.text[:100]}")

        if response.status_code == 404:
            raise AccountNotFoundError(data.get("message", "接口不存在"))

        if response.status_code >= 500:
            raise WeChatPublishError(f"服务器错误: {data.get('message', response.text)}")

        if not data.get("success", False):
            msg = data.get("message", "未知错误")
            error_code = data.get("error_code")
            raise WeChatPublishError(f"{msg} (错误码: {error_code})")

        return data

    def publish_article(self, request: PublishRequest) -> PublishResult:
        """发布文章到微信公众号草稿箱

        Args:
            request: 发布请求对象

        Returns:
            发布结果，包含 draft_id

        Raises:
            ValidationError: 参数验证失败
            SignatureError: 签名生成失败
            PublishFailedError: 发布失败
        """
        # 验证必填参数
        if not request.title or not request.content:
            raise ValidationError("title 和 content 不能为空")

        account = self._get_account(request.account)
        timestamp = int(time.time())

        # 计算 body_hash: sha256(title + content)
        body_hash_input = f"{request.title}{request.content}"
        body_hash = hashlib.sha256(body_hash_input.encode()).hexdigest()

        # 生成签名
        signature = self._make_signature(account, timestamp, body_hash)

        # 构建请求体
        payload = {
            "account": account,
            "title": request.title,
            "content": request.content,
            "timestamp": timestamp,
            "signature": signature
        }

        # 可选参数
        if request.thumb_media_id:
            payload["thumb_media_id"] = request.thumb_media_id
        if request.content_format:
            payload["content_format"] = request.content_format
        if request.theme:
            payload["theme"] = request.theme
        if request.author:
            payload["author"] = request.author
        if request.digest:
            payload["digest"] = request.digest
        if request.show_cover_pic is not None:
            payload["show_cover_pic"] = request.show_cover_pic
        if request.need_open_comment is not None:
            payload["need_open_comment"] = request.need_open_comment
        if request.only_fans_can_comment is not None:
            payload["only_fans_can_comment"] = request.only_fans_can_comment

        # 发送请求
        url = f"{self.endpoint_base}/publish"
        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout
        )

        data = self._handle_response(response)

        return PublishResult(
            success=data.get("success", False),
            message=data.get("message", ""),
            draft_id=data.get("draft_id")
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

        # 上传接口的 body_hash 固定为 "upload"
        body_hash = "upload"
        signature = self._make_signature(account, timestamp, body_hash)

        # 发送 multipart/form-data 请求
        url = f"{self.endpoint_base}/materials/upload"
        with open(request.file_path, "rb") as f:
            files = {"file": f}
            data = {
                "account": account,
                "timestamp": str(timestamp),
                "signature": signature
            }

            response = self.session.post(
                url,
                files=files,
                data=data,
                timeout=self.timeout
            )

        resp_data = self._handle_response(response)

        return UploadResult(
            success=resp_data.get("success", False),
            message=resp_data.get("message", ""),
            media_id=resp_data.get("media_id"),
            url=resp_data.get("url")
        )

    def list_materials(
        self,
        account: Optional[str] = None,
        material_type: str = "image",
        offset: int = 0,
        count: int = 20
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
        timestamp = int(time.time())

        # list 接口的 body_hash 为 material_type
        body_hash = material_type
        signature = self._make_signature(account, timestamp, body_hash)

        url = f"{self.endpoint_base}/materials/list"
        payload = {
            "account": account,
            "material_type": material_type,
            "timestamp": timestamp,
            "signature": signature,
            "offset": offset,
            "count": min(count, 20)
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout
        )

        data = self._handle_response(response)

        return MaterialsListResult(
            success=data.get("success", False),
            message=data.get("message", ""),
            total_count=data.get("total_count", 0),
            item_count=data.get("item_count", 0),
            items=data.get("items", [])
        )

    def render_markdown(self, request: RenderRequest) -> RenderResult:
        """渲染 Markdown 为微信兼容 HTML

        Args:
            request: 渲染请求对象

        Returns:
            渲染结果，包含 HTML 内容
        """
        url = f"{self.endpoint_base}/render/markdown"
        payload = {
            "content": request.content,
            "theme": request.theme
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout
        )

        data = self._handle_response(response)

        return RenderResult(
            success=data.get("success", False),
            html=data.get("html", ""),
            message=data.get("message", "")
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
        payload = {
            "content": content,
            "theme": theme
        }

        response = self.session.post(
            url,
            json=payload,
            timeout=self.timeout
        )

        data = self._handle_response(response)

        return RenderResult(
            success=data.get("success", False),
            html=data.get("html", ""),
            message=data.get("message", "")
        )
