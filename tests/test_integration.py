"""SDK 集成测试

测试基于 SDK 的接入是否成功。
所有测试通过后，可以发布 SDK。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat_publish_sdk import (
    WeChatClient,
    PublishRequest,
    UploadRequest,
    MaterialsListResult,
    RenderRequest
)
from wechat_publish_sdk.exceptions import (
    ValidationError,
    AccountNotFoundError,
    PublishFailedError,
    UploadError,
    WeChatPublishError
)


# 测试配置
BASE_URL = "http://127.0.0.1:3000"
SIGNING_KEY = os.getenv("SIGNING_KEY", "0000000000000000000000000000000000000000000000000000000000000000")
DEFAULT_ACCOUNT = "finflow"  # 使用已配置的账号


def test_connection():
    """测试连接"""
    print("=" * 60)
    print("测试 1: 连接测试")
    print("=" * 60)

    try:
        client = WeChatClient(
            base_url=BASE_URL,
            signing_key=SIGNING_KEY,
            default_account=DEFAULT_ACCOUNT,
            api_version="v1"
        )
        print(f"✅ 客户端初始化成功")
        print(f"   - 基础 URL: {client.base_url}")
        print(f"   - API 版本: {client.api_version}")
        print(f"   - 默认账号: {client.default_account}")
        print()
        return client
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        sys.exit(1)


def test_render_markdown(client):
    """测试 Markdown 渲染"""
    print("=" * 60)
    print("测试 2: Markdown 渲染")
    print("=" * 60)

    try:
        result = client.render_markdown(
            RenderRequest(
                content="# 测试标题\n\n这是测试内容\n\n- 列表项1\n- 列表项2\n- 列表项3",
                theme="orange"
            )
        )

        if result.success:
            print(f"✅ 渲染成功")
            print(f"   - HTML 长度: {len(result.html)} 字符")
            print(f"   - 消息: {result.message}")
            print(f"   - HTML 预览（前100字符）:")
            preview = result.html[:100] if len(result.html) > 100 else result.html
            print(f"   {preview}")
            print()
            return True
        else:
            print(f"❌ 渲染失败: {result.message}")
            print()
            return False

    except Exception as e:
        print(f"❌ 渲染异常: {e}")
        print()
        return False


def test_list_materials(client):
    """测试查询素材列表"""
    print("=" * 60)
    print("测试 3: 查询素材列表")
    print("=" * 60)

    try:
        result = client.list_materials(
            account=DEFAULT_ACCOUNT,
            material_type="image",
            offset=0,
            count=5
        )

        if result.success:
            print(f"✅ 查询成功")
            print(f"   - 总素材数: {result.total_count}")
            print(f"   - 返回数: {result.item_count}")
            if result.items:
                print(f"   - 前3个素材:")
                for i, item in enumerate(result.items[:3], 1):
                    print(f"     {i}. {item.media_id[:20]}...")
            print()
            return True
        else:
            print(f"❌ 查询失败: {result.message}")
            print()
            return False

    except Exception as e:
        print(f"❌ 查询异常: {e}")
        print()
        return False


def test_publish_basic(client):
    """测试基本发布（无封面）"""
    print("=" * 60)
    print("测试 4: 基本发布（无封面）")
    print("=" * 60)

    try:
        result = client.publish_article(
            PublishRequest(
                title="SDK 集成测试文章",
                content="# 文章内容\n\n这是通过 SDK 发布的测试文章。\n\n## 功能验证\n\n- SDK 初始化\n- Markdown 渲染\n- 素材查询\n- 文章发布",
                show_cover_pic=0,
                content_format="markdown",
                theme="default"
            )
        )

        if result.success:
            print(f"✅ 发布成功")
            print(f"   - draft_id: {result.draft_id}")
            print(f"   - 消息: {result.message}")
            print()
            return True
        else:
            print(f"❌ 发布失败: {result.message}")
            print()
            return False

    except ValidationError as e:
        print(f"❌ 参数验证失败: {e}")
        print()
        return False
    except AccountNotFoundError as e:
        print(f"❌ 账号不存在: {e}")
        print()
        return False
    except PublishFailedError as e:
        print(f"❌ 发布失败: {e}")
        print()
        return False
    except WeChatPublishError as e:
        print(f"❌ 其他错误: {e}")
        print()
        return False


def test_validation_error(client):
    """测试参数验证错误"""
    print("=" * 60)
    print("测试 5: 参数验证（预期失败）")
    print("=" * 60)

    try:
        # 测试空标题
        result = client.publish_article(
            PublishRequest(
                title="",  # 空标题
                content="内容",
                show_cover_pic=0
            )
        )
        print(f"❌ 预期：空标题应失败，实际结果: success={result.success}")
        print()
        return False

    except ValidationError as e:
        print(f"✅ 参数验证正常工作")
        print(f"   - 捕获到预期错误: {e}")
        print()
        return True
    except Exception as e:
        print(f"❌ 意外异常: {e}")
        print()
        return False


def main():
    """主测试流程"""
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║        WeChat Publish SDK 集成测试                   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    # 测试结果统计
    tests_passed = []
    tests_failed = []

    # 测试 1: 连接
    client = test_connection()
    if not client:
        print("\n❌ 测试终止：连接失败")
        sys.exit(1)

    # 测试 2: Markdown 渲染
    if test_render_markdown(client):
        tests_passed.append("Markdown 渲染")
    else:
        tests_failed.append("Markdown 渲染")

    # 测试 3: 查询素材列表
    if test_list_materials(client):
        tests_passed.append("素材列表查询")
    else:
        tests_failed.append("素材列表查询")

    # 测试 4: 基本发布
    if test_publish_basic(client):
        tests_passed.append("基本发布")
    else:
        tests_failed.append("基本发布")

    # 测试 5: 参数验证
    if test_validation_error(client):
        tests_passed.append("参数验证")
    else:
        tests_failed.append("参数验证")

    # 测试总结
    print()
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {len(tests_passed)}/{len(tests_passed) + len(tests_failed)}")
    print()

    if tests_passed:
        print("✅ 通过的测试:")
        for test in tests_passed:
            print(f"   - {test}")

    if tests_failed:
        print("❌ 失败的测试:")
        for test in tests_failed:
            print(f"   - {test}")

    print()

    # 判断是否可以发布
    all_critical_passed = all([
        "Markdown 渲染" in tests_passed,
        "素材列表查询" in tests_passed,
        "基本发布" in tests_passed,
    ])

    print("=" * 60)
    print("发布决策")
    print("=" * 60)

    if all_critical_passed:
        print()
        print("✅✅✅ 所有核心功能测试通过！")
        print()
        print("SDK 集成测试成功，可以发布到 PyPI。")
        print()
        print("发布后，Python 应用可以通过以下方式接入：")
        print()
        print("1. 从 PyPI 安装:")
        print("   pip install wechat-publish-sdk")
        print()
        print("2. 查看接入文档:")
        print("   https://github.com/tangcheng/wechat-publish-sdk")
        print()
        print("3. 参考示例代码:")
        print("   examples/basic_usage.py")
        sys.exit(0)
    else:
        print()
        print("❌ 存在失败的测试，SDK 暂不发布。")
        print()
        print("请检查以下事项：")
        print("1. 服务是否正常运行在 3000 端口")
        print("2. 账号配置是否正确")
        print("3. 签名密钥是否正确")
        print("4. 服务日志中是否有错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
