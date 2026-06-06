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
            "会话信息": ["get_session_info", "get_active_document_info", "get_selection_info"],
            "文档管理": ["create_document", "open_image", "save_document", "close_document", "crop_document"],
            "图层基础": [
                "create_layer",
                "delete_layer",
                "duplicate_layer",
                "merge_visible_layers",
                "flatten_image",
                "rasterize_layer",
            ],
            "图层属性": [
                "set_layer_opacity",
                "set_layer_blend_mode",
                "set_layer_visibility",
                "set_layer_locked",
                "rename_layer",
                "fill_layer",
            ],
            "图层排序": [
                "move_layer_up",
                "move_layer_down",
                "move_layer_to_top",
                "move_layer_to_bottom",
                "move_layer_to_position",
            ],
            "图层变换": ["move_layer", "scale_layer", "rotate_layer", "fit_layer_to_document", "resize_image"],
            "文字工具": [
                "create_text_layer",
                "update_text_content",
                "set_text_font",
                "set_text_color",
                "set_text_alignment",
            ],
            "滤镜": ["apply_gaussian_blur", "apply_motion_blur", "apply_sharpen", "apply_noise"],
            "调整": [
                "adjust_brightness_contrast",
                "adjust_hue_saturation",
                "auto_levels",
                "auto_contrast",
                "desaturate",
                "invert",
            ],
            "选区": ["select_all", "select_rectangle", "deselect", "invert_selection"],
            "图像操作": ["place_image", "get_layers"],
            "蒙版": ["create_layer_mask", "apply_layer_mask", "delete_layer_mask"],
            "历史记录": ["undo", "redo", "get_history"],
            "动作/脚本": ["play_action", "execute_script"],
            "批量操作": ["execute_batch", "select_layer_by_name"],
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
        print(f"预期工具数: 61")
        print(f"分类工具数: {total_categorized}")

        if len(tools) == 61:
            print()
            print("[OK] 完美！所有 61 个工具已成功注册")
        elif len(tools) > 61:
            print()
            print(f"[WARN] 警告：注册了 {len(tools) - 61} 个额外工具")
        else:
            print()
            print(f"[ERROR] 缺少 {61 - len(tools)} 个工具")

        print("=" * 60)
        print()

        # 显示所有工具的完整列表
        if len(sys.argv) > 1 and sys.argv[1] == "--all":
            print("完整工具列表（按字母顺序）:")
            print("-" * 60)
            for i, tool in enumerate(sorted(tools), 1):
                print(f"{i:2d}. {tool}")
            print()

        return len(tools) == 61

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
