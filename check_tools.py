"""检查所有工具是否正确注册"""

import sys
from pathlib import Path

# 添加项目路径到 Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_tools():
    """检查并列出所有注册的工具"""
    print("=" * 60)
    print("PSForge - 工具注册检查")
    print("=" * 60)
    print()

    try:
        from mcp.server.fastmcp import FastMCP
        from psforge.registry import discover_and_register_tools

        # 创建测试 MCP 服务器
        print("[1] 创建 MCP 服务器实例...")
        mcp = FastMCP("PSForge-ToolCheck")
        print("   [OK] MCP 服务器创建成功")
        print()

        # 发现并注册工具
        print("[2] 发现并注册工具...")
        tools = discover_and_register_tools(mcp)
        print(f"   [OK] 成功注册 {len(tools)} 个工具")
        print()

        # 按类别分组显示
        print("工具列表（按类别）:")
        print("-" * 60)

        tool_categories = {
            "会话信息": ["get_session_info"],
            "检查/反馈": ["get_layers", "capture_canvas"],
            "脚本执行": ["execute_script", "execute_batch"],
            "高层工作流": ["recreate_image_as_layered_psd"],
        }

        total_categorized = 0
        for category, expected_tools in tool_categories.items():
            found_tools = [t for t in expected_tools if t in tools]
            missing_tools = [t for t in expected_tools if t not in tools]

            print(f"\n{category} ({len(found_tools)}/{len(expected_tools)}):")
            for tool in found_tools:
                print(f"  [OK] {tool}")
            for tool in missing_tools:
                print(f"  [MISSING] {tool}")

            total_categorized += len(expected_tools)

        # 检查未分类的工具
        categorized_set = set()
        for cat_tools in tool_categories.values():
            categorized_set.update(cat_tools)

        uncategorized = [t for t in tools if t not in categorized_set]
        if uncategorized:
            print(f"\n未分类工具 ({len(uncategorized)}):")
            for tool in uncategorized:
                print(f"  [WARN] {tool}")

        # 总结
        print()
        print("=" * 60)
        print("统计信息:")
        print("-" * 60)
        print(f"实际注册工具数: {len(tools)}")
        expected_count = 6
        print(f"预期工具数: {expected_count}")
        print(f"分类工具数: {total_categorized}")

        if len(tools) == expected_count:
            print()
            print(f"[OK] 完美！所有 {expected_count} 个工具已成功注册")
        elif len(tools) > expected_count:
            print()
            print(f"[WARN] 警告：注册了 {len(tools) - expected_count} 个额外工具")
        else:
            print()
            print(f"[ERROR] 缺少 {expected_count - len(tools)} 个工具")

        print("=" * 60)
        print()

        # 显示所有工具的完整列表
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            print("完整工具列表（按字母顺序）:")
            print("-" * 60)
            for i, tool in enumerate(sorted(tools), 1):
                print(f"{i:2d}. {tool}")
            print()

        return len(tools) == expected_count

    except Exception as e:
        print(f"[ERROR] 检查失败: {e}")
        print()
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("提示: 使用 'python check_tools.py --all' 查看完整工具列表")
    print()

    success = check_tools()
    sys.exit(0 if success else 1)
