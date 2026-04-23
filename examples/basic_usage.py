"""基础使用示例"""
import os
from wechat_publish_sdk import WeChatClient, PublishRequest, UploadRequest, RenderRequest


def main():
    # 初始化客户端
    client = WeChatClient(
        base_url="http://localhost:3000",
        signing_key=os.getenv("SIGNING_KEY", "0000000000000000000000000000000000000000000000000000000000000000"),
        default_account="mingdeng",
        api_version="v1"
    )

    print("=== 示例 1: 基本发布 ===")
    try:
        result = client.publish_article(
            PublishRequest(
                title="SDK 测试文章",
                content="# 这是通过 SDK 发布的文章\n\n欢迎使用 WeChat Publish SDK！"
            )
        )
        if result.success:
            print(f"✅ 发布成功，draft_id: {result.draft_id}")
        else:
            print(f"❌ 发布失败: {result.message}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n=== 示例 2: 带封面的发布 ===")
    try:
        # 注意：实际使用时需要提供真实的图片路径
        upload_result = client.upload_image(
            UploadRequest(
                account="mingdeng",
                file_path="/tmp/test_cover.jpg"
            )
        )

        if upload_result.success:
            media_id = upload_result.media_id
            print(f"✅ 封面上传成功，media_id: {media_id}")

            result = client.publish_article(
                PublishRequest(
                    title="带封面的文章",
                    content="# 文章内容\n\n这里是正文...",
                    thumb_media_id=media_id,
                    show_cover_pic=1,
                    author="SDK 作者",
                    digest="这是文章摘要"
                )
            )
            if result.success:
                print(f"✅ 文章发布成功，draft_id: {result.draft_id}")
        else:
            print(f"❌ 封面上传失败: {upload_result.message}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n=== 示例 3: 查询素材列表 ===")
    try:
        result = client.list_materials(
            account="mingdeng",
            material_type="image",
            offset=0,
            count=5
        )
        if result.success:
            print(f"✅ 共 {result.total_count} 个素材，当前显示 {result.item_count} 个")
            for item in result.items[:3]:
                print(f"  - {item.media_id}: {item.name}")
        else:
            print(f"❌ 查询失败: {result.message}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    print("\n=== 示例 4: Markdown 渲染 ===")
    try:
        result = client.render_markdown(
            RenderRequest(
                content="# 标题\n\n这是测试内容\n\n- 列表1\n- 列表2",
                theme="orange"
            )
        )
        if result.success:
            print("✅ 渲染成功")
            print("HTML 内容:")
            print(result.html[:200] + "..." if len(result.html) > 200 else result.html)
        else:
            print(f"❌ 渲染失败: {result.message}")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
