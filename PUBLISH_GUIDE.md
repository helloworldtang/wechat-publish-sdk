# wechat-publish-sdk PyPI 发布指南

## 当前状态

✅ SDK 已成功构建
- `wechat_publish_sdk-1.0.0.tar.gz` - 源码包
- `wechat_publish_sdk-1.0.0-py3-none-any.whl` - Wheel 包

## 发布到 PyPI

### 方法 1: 使用 twine（推荐）

```bash
cd /Users/tangcheng/workspace/github/wechat-publish-sdk

# 1. 安装 twine
pip install twine

# 2. 检查包内容
twine check dist/*

# 3. 上传到 PyPI (测试环境，可选)
twine upload --repository testpypi dist/*

# 4. 上传到 PyPI (生产环境)
twine upload dist/*
```

### 方法 2: 使用 uv

```bash
cd /Users/tangcheng/workspace/github/wechat-publish-sdk

# 上传到 PyPI
uv publish dist/*
```

## PyPI 凭备

首次发布需要：
1. 注册 PyPI 账号：https://pypi.org/account/register/
2. 启用双因素认证（2FA）
3. 生成 API Token：https://pypi.org/manage/account/token/

## 版本管理

### 发布新版本

1. 更新 `pyproject.toml` 中的版本号
2. 构建新包：`python3 -m build`
3. 上传到 PyPI：`twine upload dist/*`

### 版本号规则

- `1.0.0` → `1.0.1` (bug 修复)
- `1.0.0` → `1.1.0` (新功能)
- `1.0.0` → `2.0.0` (破坏性变更)

## 测试安装

发布后用户可以这样安装：

```bash
pip install wechat-publish-sdk
```

或指定版本：

```bash
pip install wechat-publish-sdk==1.0.0
```

或从测试环境安装：

```bash
pip install --index-url https://test.pypi.org/simple/ wechat-publish-sdk
```

## SDK 内容

- `client.py` - WeChatClient 主客户端
- `models.py` - 数据模型定义
- `exceptions.py` - 异常类
- `__init__.py` - 包导出

## 依赖

- `requests>=2.28.0`

## 使用示例

```python
from wechat_publish_sdk import WeChatClient, PublishRequest

client = WeChatClient(
    base_url="http://localhost:3000",
    api_key="sk_live_xxx",
    signing_key="xxx",
    default_account="finflow"
)

result = client.publish_article(
    PublishRequest(
        title="测试文章",
        content="# 内容"
    )
)
```
