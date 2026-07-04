# WeChat Publish SDK

微信公众号发布服务的 Python SDK，提供稳定、易用的 API 接口。

后端服务 [wechat-publish-service](https://github.com/helloworldtang/wechat-publish-service) 已部署在 [yyps.net](https://yyps.net)，统一接入 [ai-as.cc](https://ai-as.cc) OIDC 认证中台。

## 特性

- ✅ **M2M 双认证** — API Key（`X-API-Key`，推荐）或 OIDC（`Authorization: Bearer`，`client_credentials`）
- ✅ **类型安全** — 完整类型注解，IDE 提示友好
- ✅ **自动 OIDC 刷新** — token 过期前自动刷新，线程安全
- ✅ **统一异常体系** — 清晰的错误处理
- ✅ **默认账号** — 设置 `default_account` 后无需每次传 account

## 安装

```bash
pip install wechat-publish-sdk
```

## 快速开始

### 方式一：API Key（推荐）

从 ai-as.cc 申请 API Key，service 侧通过 ai-as.cc `/api/keys/validate` 验证，一行配置即可。

```python
from wechat_publish_sdk import WeChatClient, PublishRequest

client = WeChatClient(
    base_url="https://yyps.net",
    api_key="sk_live_xxx",          # 从 ai-as.cc 申请
    default_account="mingdeng",
)

result = client.publish_article(
    PublishRequest(title="测试文章", content="# 这是测试内容")
)
if result.success:
    print(f"发布成功，draft_id: {result.draft_id}")
```

### 方式二：OIDC（`client_credentials`）

适合需要标准 OAuth2 token 的场景。SDK 内置 OIDC 客户端，自动 discovery + 刷新。

```python
from wechat_publish_sdk import WeChatClient, PublishRequest, OIDCConfig

client = WeChatClient(
    base_url="https://yyps.net",
    oidc=OIDCConfig(
        client_id="your_client_id",
        client_secret="your_client_secret",
        # issuer 默认即 https://auth.ai-as.cc
    ),
    default_account="mingdeng",
)

result = client.publish_article(
    PublishRequest(title="测试文章", content="# 内容")
)
```

> **前置条件**：OIDC Bearer 端到端生效依赖 service 侧 `/api/mp/publish` 支持 Bearer 认证。

### 上传素材

```python
from wechat_publish_sdk import UploadRequest

upload = client.upload_image(UploadRequest(file_path="path/to/cover.jpg"))
if upload.success:
    media_id = upload.media_id
```

### 查询素材列表

```python
result = client.list_materials(material_type="image", offset=0, count=20)
if result.success:
    for item in result.items:
        print(f"  - {item.name}: {item.url}")
```

### Markdown 渲染

```python
from wechat_publish_sdk import RenderRequest

result = client.render_markdown(
    RenderRequest(content="# 标题\n\n内容", theme="orange")
)
if result.success:
    print(result.html)
```

## 认证说明

SDK 定位 M2M（机器对机器），提供两条并行认证路径，**均对接 ai-as.cc**，二选一：

| 方式 | 入参 | 请求头 | service 侧验证 |
| --- | --- | --- | --- |
| **API Key**（推荐） | `api_key` | `X-API-Key` | 调 ai-as.cc `/api/keys/validate` |
| **OIDC** | `oidc=OIDCConfig(...)` | `Authorization: Bearer` | 本地 JWKS 验签（RS256） |
| ~~签名~~（已废弃） | `signing_key` | — | service 已不校验，传入会触发 `DeprecationWarning` |

## 配置说明

### 环境变量（推荐）

```env
WECHAT_PUBLISH_URL=https://yyps.net
API_KEY=sk_live_xxx
# 或使用 OIDC
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
DEFAULT_ACCOUNT=mingdeng
```

```python
import os
from wechat_publish_sdk import WeChatClient, OIDCConfig

client = WeChatClient(
    base_url=os.getenv("WECHAT_PUBLISH_URL"),
    api_key=os.getenv("API_KEY"),
    # 或 oidc=OIDCConfig(os.environ["OIDC_CLIENT_ID"], os.environ["OIDC_CLIENT_SECRET"]),
    default_account=os.getenv("DEFAULT_ACCOUNT"),
)
```

### 客户端参数

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `base_url` | str | 是 | 后端服务地址，如 `https://yyps.net` |
| `api_key` | str | 三选一 | API Key |
| `oidc` | `OIDCConfig` | 三选一 | OIDC 配置 |
| `signing_key` | str | 三选一 | 已废弃 |
| `default_account` | str | 否 | 默认账号 |
| `api_version` | str | 否 | API 版本，默认 `v1` |
| `timeout` | int | 否 | 请求超时（秒），默认 30 |

## 异常处理

```python
from wechat_publish_sdk import (
    WeChatClient, PublishRequest,
    ValidationError, AccountNotFoundError, PublishFailedError, WeChatPublishError,
)

try:
    result = client.publish_article(PublishRequest(...))
except ValidationError as e:
    print(f"参数错误: {e}")
except AccountNotFoundError as e:
    print(f"账号不存在: {e}")
except PublishFailedError as e:
    print(f"发布失败: {e}")
except WeChatPublishError as e:
    print(f"其他错误: {e}")
```

## 安全建议

⚠️ **重要安全注意事项：**

1. **不要硬编码密钥**：永远不要在代码中硬编码 `api_key` / `client_secret`
2. **使用环境变量**：通过 `.env` 文件或系统环境变量管理凭据
3. **保护 .env 文件**：确保 `.env` 已加入 `.gitignore`（本仓库已配置）
4. **生产环境**：使用密钥管理服务（AWS Secrets Manager、HashiCorp Vault）

## 开发

```bash
git clone https://github.com/helloworldtang/wechat-publish-sdk.git
cd wechat-publish-sdk
pip install -e ".[dev]"

pytest            # 单元测试
python -m build   # 构建产物
black src/        # 格式化
mypy src/         # 类型检查
```

## License

MIT License
