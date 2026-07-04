"""基础使用示例

演示 API Key 与 OIDC 两种 M2M 认证方式。运行前设置环境变量：
  - WECHAT_PUBLISH_URL（默认 https://yyps.net）
  - API_KEY（方式一），或 OIDC_CLIENT_ID + OIDC_CLIENT_SECRET（方式二）
  - DEFAULT_ACCOUNT（默认 mingdeng）
"""
import os

from wechat_publish_sdk import (
    WeChatClient, PublishRequest, RenderRequest, OIDCConfig,
)


def build_client() -> WeChatClient:
    """根据环境变量选择认证方式构建客户端"""
    base_url = os.getenv("WECHAT_PUBLISH_URL", "https://yyps.net")
    default_account = os.getenv("DEFAULT_ACCOUNT", "mingdeng")

    if os.getenv("OIDC_CLIENT_ID") and os.getenv("OIDC_CLIENT_SECRET"):
        # 方式二：OIDC（client_credentials）
        return WeChatClient(
            base_url=base_url,
            oidc=OIDCConfig(
                client_id=os.environ["OIDC_CLIENT_ID"],
                client_secret=os.environ["OIDC_CLIENT_SECRET"],
            ),
            default_account=default_account,
        )

    # 方式一：API Key（默认推荐）
    return WeChatClient(
        base_url=base_url,
        api_key=os.getenv("API_KEY", "sk_live_xxx"),
        default_account=default_account,
    )


def main():
    client = build_client()

    print("=== 示例 1: 基本发布 ===")
    try:
        result = client.publish_article(
            PublishRequest(
                title="SDK 测试文章",
                content="# 通过 SDK 发布\n\n欢迎使用 WeChat Publish SDK！",
            )
        )
        status = "✅" if result.success else "❌"
        print(f"{status} {result.message} draft_id={result.draft_id}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n=== 示例 2: 查询素材列表 ===")
    try:
        result = client.list_materials(material_type="image", offset=0, count=5)
        if result.success:
            print(f"✅ 共 {result.total_count} 个素材")
            for item in result.items[:3]:
                print(f"  - {item.media_id}: {item.name}")
        else:
            print(f"❌ {result.message}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n=== 示例 3: Markdown 渲染 ===")
    try:
        result = client.render_markdown(
            RenderRequest(content="# 标题\n\n内容", theme="orange")
        )
        status = "✅" if result.success else "❌"
        print(f"{status} {result.message}")
        if result.success:
            print(result.html[:200])
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
