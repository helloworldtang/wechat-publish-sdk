# CLAUDE.md — wechat-publish-sdk

本文件为 Claude Code 提供项目上下文。

## ⚠️ Git 提交规则（强制）

**提交本仓库时，禁止添加任何形式的 `Co-Authored-By` trailer**（包括 Claude / Anthropic / `noreply@anthropic.com`）。

历史已通过 `git filter-repo` 清理过一次。commit message 只描述改动本身，不加 AI 协作署名——AI 署名会降低仓库的专业性与可信度。

## 项目概述

`wechat-publish-sdk` 是微信公众号发布服务 [wechat-publish-service](https://github.com/helloworldtang/wechat-publish-service) 的 Python 客户端。service 已部署在 [yyps.net](https://yyps.net)，统一接入 [ai-as.cc](https://ai-as.cc)（Auth Center · OIDC 统一认证授权中台，认证域 `auth.ai-as.cc`）。

## 目录结构（src layout）

```
src/wechat_publish_sdk/        # 包源码（pip install -e . 后可 import）
  __init__.py                  # 版本号唯一来源（__version__）+ 公开 API
  client.py                    # WeChatClient 核心
  models.py                    # 请求/响应 dataclass
  exceptions.py                # 异常体系
  oidc.py                      # 内置 OIDC 客户端（client_credentials）
tests/                         # pytest 单元测试
examples/                      # 使用示例
.github/workflows/publish.yml  # PyPI Trusted Publishing（tag v* 触发）
```

## 认证架构（M2M 双路径，二选一）

均对接 ai-as.cc，互斥：

- **API Key**（推荐）：`WeChatClient(api_key=...)` → `X-API-Key` 头；service 调 ai-as.cc `/api/keys/validate` 验证。
- **OIDC**（可选）：`WeChatClient(oidc=OIDCConfig(client_id, client_secret))` → `Authorization: Bearer`；SDK 内置 `client_credentials` 客户端对接 `auth.ai-as.cc`，token 过期前自动刷新（线程安全）。
- `signing_key`：已废弃，传入触发 `DeprecationWarning`，service 不再校验。

> 前置条件：OIDC Bearer 端到端生效依赖 service 侧 `/api/mp/publish` 支持 Bearer 认证。

## 开发命令

```bash
pip install -e ".[dev]"   # 可编辑安装（含 dev 依赖）
pytest                    # 单元测试
python -m build           # 构建 wheel + sdist
black src/                # 格式化
mypy src/                 # 类型检查
```

## 发布

通过 git tag 触发 GitHub Actions → PyPI Trusted Publishing：

```bash
# 1. 更新 src/wechat_publish_sdk/__init__.py 的 __version__
# 2. 提交（不加 Co-Authored-By）
# 3. 打 tag 并推送
git tag v1.x.y
git push origin v1.x.y
```

注意：PyPI 已发布的版本不可覆盖、不可删除单个 release；新发布需 bump 版本号。

## 版本管理

版本号**唯一来源**是 `src/wechat_publish_sdk/__init__.py` 的 `__version__`；`pyproject.toml` 通过 `dynamic = ["version"]` + `[tool.setuptools.dynamic]` 读取。改版本只改 `__init__.py`。

## 禁止混入的文件（属于 service 仓库，非 SDK）

`miniprogram.db`、`migrations/`、`*.db`、`.env` 已加入 `.gitignore`。这些属于 wechat-publish-service，不要提交到本 SDK 仓库。
