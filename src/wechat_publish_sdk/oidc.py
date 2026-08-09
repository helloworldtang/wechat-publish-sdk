"""OIDC 客户端：对接 ai-as.cc 统一认证授权中台（auth.ai-as.cc）

提供 M2M（机器对机器）场景下的 OAuth2 ``client_credentials`` 流程，
自动发现 issuer、获取 access_token、并在过期前自动刷新。

SDK 使用方通常无需直接操作本模块——在构造 :class:`WeChatClient` 时
传入 :class:`OIDCConfig` 即可启用 Bearer 认证。
"""

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from .exceptions import AuthenticationError


# 默认对接 ai-as.cc 统一认证授权中台
DEFAULT_ISSUER = "https://auth.ai-as.cc"
_DISCOVERY_PATH = "/.well-known/openid-configuration"

# 提前刷新阈值（秒）：token 还剩该时间就主动刷新，避免请求途中过期
_REFRESH_LEEWAY = 30

# discovery 响应缺失 expires_in 时的保守有效期（秒）
_DEFAULT_TTL = 600


@dataclass
class OIDCConfig:
    """OIDC 客户端配置

    Args:
        client_id: 在 ai-as.cc 注册的客户端 ID
        client_secret: 客户端密钥
        issuer: OIDC 签发方，默认 ``https://auth.ai-as.cc``
        scope: 申请的权限范围，默认 ``openid publish:write``
        token_endpoint: 可选，直接指定 token 端点，跳过 discovery
    """

    client_id: str
    client_secret: str
    issuer: str = DEFAULT_ISSUER
    scope: str = "openid publish:write"
    token_endpoint: Optional[str] = None


class OIDCClient:
    """内置 OIDC 客户端，封装 token 获取与自动刷新

    使用 ``client_credentials`` 授权（适合无终端用户参与的发布场景）。
    线程安全：并发调用 :meth:`get_valid_token` 不会重复请求 token 端点。
    """

    def __init__(
        self,
        config: OIDCConfig,
        session: Optional[requests.Session] = None,
        timeout: int = 10,
    ) -> None:
        self.config = config
        self.timeout = timeout
        # 复用主 client 的 Session 以共享连接池与 trust_env 策略
        self._session = session if session is not None else requests.Session()
        self._session.trust_env = False
        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._refresh_token: Optional[str] = None

    def _resolve_token_endpoint(self) -> str:
        """解析 token 端点：优先用配置，否则走 OIDC discovery 并缓存"""
        if self.config.token_endpoint:
            return self.config.token_endpoint
        url = f"{self.config.issuer.rstrip('/')}{_DISCOVERY_PATH}"
        resp = self._session.get(url, timeout=self.timeout)
        if resp.status_code != 200:
            raise AuthenticationError(
                f"OIDC discovery 失败 ({resp.status_code}): {resp.text[:120]}"
            )
        try:
            doc = resp.json()
        except ValueError as error:
            raise AuthenticationError("OIDC discovery 返回非 JSON 响应") from error
        endpoint = doc.get("token_endpoint")
        if not endpoint:
            raise AuthenticationError("OIDC discovery 文档缺少 token_endpoint")
        # 缓存，后续直接复用
        self.config.token_endpoint = endpoint
        return endpoint

    def _request_token(
        self, grant_type: str, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """向 token 端点发起一次请求"""
        endpoint = self._resolve_token_endpoint()
        data: Dict[str, Any] = {
            "grant_type": grant_type,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.config.scope,
        }
        if extra:
            data.update(extra)
        resp = self._session.post(endpoint, data=data, timeout=self.timeout)
        if resp.status_code != 200:
            raise AuthenticationError(
                f"获取 token 失败 ({resp.status_code}): {resp.text[:200]}"
            )
        try:
            payload = resp.json()
        except ValueError as error:
            raise AuthenticationError("token 端点返回非 JSON 响应") from error
        if "access_token" not in payload:
            raise AuthenticationError(f"token 响应缺少 access_token: {payload}")
        return payload

    def _store(self, payload: Dict[str, Any]) -> str:
        """从 token 响应中提取并缓存 access_token / 过期时间 / refresh_token"""
        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in")
        if expires_in is None:
            expires_in = _DEFAULT_TTL
        self._expires_at = time.time() + float(expires_in)
        # refresh_token 可选；保留最新的，没有则沿用旧的
        if "refresh_token" in payload:
            self._refresh_token = payload["refresh_token"]
        return self._access_token

    def fetch_token(self) -> str:
        """走 ``client_credentials`` 获取全新的 access_token"""
        return self._store(self._request_token("client_credentials"))

    def refresh(self) -> str:
        """刷新 token：有 refresh_token 则刷新，否则回退到 client_credentials"""
        if self._refresh_token:
            try:
                return self._store(
                    self._request_token(
                        "refresh_token",
                        {"refresh_token": self._refresh_token},
                    )
                )
            except AuthenticationError:
                # refresh_token 失效等情况，回退到重新获取
                pass
        return self.fetch_token()

    def get_valid_token(self) -> str:
        """返回未过期的 access_token；过期则在锁内自动刷新/重新获取"""
        with self._lock:
            if self._access_token and time.time() < self._expires_at - _REFRESH_LEEWAY:
                return self._access_token
            # 已有 token（含 refresh_token）优先 refresh，首次获取走 fetch
            if self._access_token or self._refresh_token:
                return self.refresh()
            return self.fetch_token()
