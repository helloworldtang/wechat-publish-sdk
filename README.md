# WeChat Publish SDK

微信公众号发布服务的 Python SDK，提供稳定、易用的 API 接口。

## 特性

- ✅ **API 版本化** - 通过 `api_version` 参数支持多个版本
- ✅ **自动签名** - 无需手动计算 HMAC-SHA256 签名
- ✅ **类型安全** - 完整的类型注解，IDE 提示友好
- ✅ **错误处理** - 统一的异常体系
- ✅ **简洁易用** - 一个客户端解决所有操作
- ✅ **默认账号** - 设置 `default_account` 后无需每次传 account

## 安装

```bash
pip install wechat-publish-sdk
```

## 快速开始

### 1. 环境变量配置

创建 `.env` 文件（**重要：不要提交到版本控制**）：

```env
# 服务地址
WECHAT_PUBLISH_URL=http://localhost:3000

# 签名密钥（从服务端获取）
SIGNING_KEY=your_signing_key_here

# 默认账号（可选）
DEFAULT_ACCOUNT=your_account_name
```

### 2. 初始化客户端

```python
import os
from dotenv import load_dotenv
from wechat_publish_sdk import WeChatClient

# 加载环境变量
load_dotenv()

client = WeChatClient(
    base_url=os.getenv("WECHAT_PUBLISH_URL"),
    signing_key=os.getenv("SIGNING_KEY"),
    default_account=os.getenv("DEFAULT_ACCOUNT"),
    api_version="v1"
)
```

### 发布文章

```python
from wechat_publish_sdk import WeChatClient, PublishRequest

# 基本发布
result = client.publish_article(
    PublishRequest(
        title="测试文章",
        content="# 这是测试内容"
    )
)

if result.success:
    print(f"发布成功，draft_id: {result.draft_id}")
else:
    print(f"发布失败: {result.message}")
```

### 发布带封面的文章

```python
# 先上传封面
upload_result = client.upload_image(
    UploadRequest(
        account="mingdeng",
        file_path="path/to/cover.jpg"
    )
)

if upload_result.success:
    media_id = upload_result.media_id

    # 发布文章时使用封面
    result = client.publish_article(
        PublishRequest(
            title="带封面的文章",
            content="# 文章内容",
            thumb_media_id=media_id,
            show_cover_pic=1,
            author="作者名",
            digest="文章摘要"
        )
    )
```

### 批量发布

```python
articles = [
    {"title": "文章1", "content": "内容1"},
    {"title": "文章2", "content": "内容2"},
    {"title": "文章3", "content": "内容3"},
]

for article in articles:
    result = client.publish_article(
        PublishRequest(**article)
    )
    print(f"{article['title']}: {result.message}")
```

### 查询素材列表

```python
result = client.list_materials(
    account="mingdeng",
    material_type="image",
    offset=0,
    count=20
)

if result.success:
    print(f"共 {result.total_count} 个素材")
    for item in result.items:
        print(f"  - {item.name}: {item.url}")
```

### Markdown 渲染

```python
from wechat_publish_sdk import RenderRequest

result = client.render_markdown(
    RenderRequest(
        content="# 标题\n\n内容",
        theme="orange"
    )
)

if result.success:
    print(result.html)
```

## API 版本控制

SDK 支持多版本 API，通过初始化时指定 `api_version` 参数：

```python
# 使用 v1 稳定版
client_v1 = WeChatClient(
    base_url="http://localhost:3000",
    signing_key="key",
    api_version="v1"
)

# 使用 dev 开发版
client_dev = WeChatClient(
    base_url="http://localhost:3000",
    signing_key="key",
    api_version="dev"
)
```

## 异常处理

```python
from wechat_publish_sdk import (
    WeChatClient, PublishRequest,
    ValidationError, AccountNotFoundError, PublishFailedError
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

## 配置说明

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| WECHAT_PUBLISH_URL | 是 | 后端服务地址 |
| SIGNING_KEY | 是 | HMAC 签名密钥（从服务端获取）|
| DEFAULT_ACCOUNT | 否 | 默认账号 |

### 客户端参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| base_url | str | 是 | 后端服务地址 |
| signing_key | str | 是 | HMAC 签名密钥（十六进制）|
| default_account | str | 否 | 默认账号 |
| api_version | str | 否 | API 版本，默认 "v1" |
| timeout | int | 否 | 请求超时（秒），默认 30 |

## 安全建议

⚠️ **重要安全注意事项：**

1. **不要硬编码密钥**：永远不要在代码中硬编码 `SIGNING_KEY`
2. **使用环境变量**：通过 `.env` 文件或系统环境变量管理密钥
3. **保护 .env 文件**：确保 `.env` 已添加到 `.gitignore`
4. **生产环境**：使用密钥管理服务（AWS Secrets Manager、HashiCorp Vault）
5. **最小权限**：为不同项目使用不同的签名密钥

## 开发

```bash
# 克隆项目
git clone https://github.com/tangcheng/wechat-publish-sdk.git

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black wechat_publish_sdk/

# 类型检查
mypy wechat_publish_sdk/
```

## License

MIT License
