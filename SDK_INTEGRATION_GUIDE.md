# WeChat Publish SDK 接入文档

## 概述

本文档描述如何使用 `wechat-publish-sdk` 接入微信公众号发布服务。

## 前置要求

### 环境要求

- Python 3.8+
- pip 包管理器

### 服务要求

- Rust 服务已部署并运行在指定端口
- 服务端点地址可访问
- 已配置签名密钥

## 安装 SDK

### 从 PyPI 安装（推荐）

```bash
pip install wechat-publish-sdk
```

### 从源码安装（开发模式）

```bash
git clone https://github.com/tangcheng/wechat-publish-sdk.git
cd wechat-publish-sdk
pip install -e .
```

## 快速开始

### 1. 配置环境变量

创建 `.env` 文件（**添加到 .gitignore**）：

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

# 初始化客户端
client = WeChatClient(
    base_url=os.getenv("WECHAT_PUBLISH_URL"),
    signing_key=os.getenv("SIGNING_KEY"),
    default_account=os.getenv("DEFAULT_ACCOUNT")
)
```

### 2. 发布文章

#### 基础发布

```python
from wechat_publish_sdk import WeChatClient, PublishRequest

client = WeChatClient(
    base_url=os.getenv("WECHAT_PUBLISH_URL"),
    signing_key=os.getenv("SIGNING_KEY"),
    default_account=os.getenv("DEFAULT_ACCOUNT")
)

result = client.publish_article(
    PublishRequest(
        title="测试文章标题",
        content="# 这是文章内容\n\n包含 Markdown 格式",
        content_format="markdown",
        theme="orange",
        author="作者名称"
    )
)

if result.success:
    print(f"发布成功，draft_id: {result.draft_id}")
else:
    print(f"发布失败：{result.message}")
```

#### 带封面的发布

```python
# 步骤1：上传封面
upload_result = client.upload_image(
    UploadRequest(
        file_path="/path/to/cover.jpg"
    )
)

if upload_result.success:
    media_id = upload_result.media_id
    print(f"封面上传成功，media_id: {media_id}")

    # 步骤2：发布文章
    result = client.publish_article(
        PublishRequest(
            title="带封面的文章",
            content="# 文章内容",
            thumb_media_id=media_id,
            show_cover_pic=1,
            author="作者",
            digest="文章摘要",
            need_open_comment=1,
            only_fans_can_comment=0
        )
    )

    if result.success:
        print(f"发布成功")
else:
    print(f"封面上传失败：{upload_result.message}")
```

### 3. 查询素材列表

```python
result = client.list_materials(
    material_type="image",
    offset=0,
    count=20
)

if result.success:
    print(f"共 {result.total_count} 个素材")
    for item in result.items:
        print(f"  - {item.name}: {item.url}")
else:
    print(f"查询失败：{result.message}")
```

### 4. Markdown 渲染

```python
from wechat_publish_sdk import RenderRequest

result = client.render_markdown(
    RenderRequest(
        content="# 标题\n\n段落内容\n- 列表项1\n- 列表项2",
        theme="orange"
    )
)

if result.success:
    print(result.html)
else:
    print(f"渲染失败：{result.message}")
```

## 参数说明

### PublishRequest（发布文章）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| account | str | 否* | 账号标识，未设置则使用 default_account |
| title | str | 是 | 文章标题 |
| content | str | 是 | 文章内容 |
| content_format | str | 否 | 内容格式：`markdown` 或 `html`，默认 `markdown` |
| theme | str | 否 | 主题名称，如 `orange`, `blue`, `green` |
| thumb_media_id | str | 否 | 封面素材 ID |
| show_cover_pic | int | 否 | 是否显示封面，0 或 1，默认 1 |
| author | str | 否 | 作者名称 |
| digest | str | 否 | 文章摘要 |
| need_open_comment | int | 否 | 是否开启评论，默认 1 |
| only_fans_can_comment | int | 否 | 是否仅粉丝可评论，默认 0 |

### UploadRequest（上传素材）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| account | str | 否* | 账号标识 |
| file_path | str | 是 | 图片文件路径 |

### MaterialsListResult（素材列表）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| account | str | 否* | 账号标识 |
| material_type | str | 否 | 素材类型，默认 `image` |
| offset | int | 否 | 起始偏移，默认 0 |
| count | int | 否 | 数量，默认 20（最大 20）|

### RenderRequest（渲染）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | str | 是 | Markdown 或 HTML 内容 |
| theme | str | 否 | 主题名称，默认 `default` |

## 异常处理

SDK 定义了以下异常，建议按需捕获：

```python
from wechat_publish_sdk import (
    WeChatClient,
    PublishRequest,
    ValidationError,      # 参数验证失败
    AccountNotFoundError,  # 账号不存在
    PublishFailedError,    # 发布失败
    UploadError,          # 上传失败
    SignatureError,       # 签名验证失败
    WeChatPublishError     # 基础异常
)

try:
    result = client.publish_article(PublishRequest(...))
except ValidationError as e:
    print(f"参数错误：{e}")
except AccountNotFoundError as e:
    print(f"账号不存在：{e}")
except PublishFailedError as e:
    print(f"发布失败：{e}")
except UploadError as e:
    print(f"上传失败：{e}")
except WeChatPublishError as e:
    print(f"其他错误：{e}")
```

## API 版本控制

SDK 支持 API 版本控制，建议使用明确版本：

```python
# v1 稳定版（推荐生产使用）
client_v1 = WeChatClient(
    base_url="http://localhost:3000",
    signing_key="key",
    api_version="v1"  # 明确指定
)

# dev 开发版
client_dev = WeChatClient(
    base_url="http://localhost:3000",
    signing_key="key",
    api_version="dev"
)
```

**推荐策略：**
- 生产环境使用 `api_version="v1"`，锁定稳定版本
- 新版本发布后，SDK 和后端需同步升级
- 废弃版本会返回明确的废弃提示

## 配置管理

### 环境变量配置

```python
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

client = WeChatClient(
    base_url=os.getenv("WECHAT_PUBLISH_URL"),
    signing_key=os.getenv("SIGNING_KEY"),
    default_account=os.getenv("DEFAULT_ACCOUNT")
)
```

### .env 文件示例

```env
# 服务地址
WECHAT_PUBLISH_URL=http://localhost:3000

# 签名密钥（从服务端获取，十六进制格式）
SIGNING_KEY=your_signing_key_here

# 默认账号（可选）
DEFAULT_ACCOUNT=your_account_name
```

**⚠️ 安全注意事项：**

1. **不要提交 .env 文件**：确保 `.env` 已添加到 `.gitignore`
2. **使用不同密钥**：开发、测试、生产环境使用不同的签名密钥
3. **定期轮换密钥**：定期更换签名密钥以提高安全性
4. **权限控制**：设置 `.env` 文件权限为 `600`（仅所有者可读写）

## 常见问题

### Q: 如何获取签名密钥？

A: 签名密钥由服务端配置，从服务管理员获取。密钥是 64 字节的十六进制字符串。

### Q: 如何处理签名验证失败？

A: 确保以下几点：
1. `SIGNING_KEY` 环境变量正确设置
2. 密钥与服务端完全一致（复制时注意不要有多余空格）
3. 密钥格式为十六进制字符串

### Q: 如何获取账号凭证？

A: 签名密钥（`signing_key`）用于 API 请求签名，账号凭证（`appid`/`appsecret`）由后端内部管理。SDK 使用 `account` 参数来标识使用哪个账号。

### Q: 如何批量发布？

A: 遍历文章列表，逐个调用 `publish_article`：

```python
articles = [
    {"title": "文章1", "content": "内容1"},
    {"title": "文章2", "content": "内容2"},
]

for article in articles:
    result = client.publish_article(
        PublishRequest(**article)
    )
    if result.success:
        print(f"✅ {article['title']}: 发布成功")
    else:
        print(f"❌ {article['title']}: {result.message}")
```

### Q: API 版本变化时怎么办？

A:
1. SDK 保持向后兼容
2. 使用 `api_version` 参数指定版本
3. 查看版本升级说明

## 性能优化建议

1. **连接复用**：SDK 内部使用 `requests.Session()`，自动复用 TCP 连接
2. **超时控制**：根据网络环境调整 `timeout` 参数
3. **批量处理**：大量操作时考虑异步或并发

## 安全建议

1. **密钥管理**：不要在代码中硬编码签名密钥，使用环境变量或密钥管理服务
2. **HTTPS**：生产环境使用 HTTPS 端点
3. **错误日志**：妥善处理异常，避免泄露敏感信息
4. **依赖更新**：定期更新依赖包修复安全漏洞

## 支持与反馈

- 文档问题：提交 Issue
- 功能请求：提交 Feature Request
- Bug 报告：提交 Bug Report
- 联系方式：查看项目 README

---

**版本：** 1.0.0
**更新日期：** 2024-04-22
