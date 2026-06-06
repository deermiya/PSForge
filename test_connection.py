"""快速连接测试 - 验证 PSForge 与 Photoshop 的连接"""

import sys
from pathlib import Path

# 添加项目路径到 Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_connection():
    """测试与 Photoshop 的基本连接"""
    print("=" * 60)
    print("PSForge - Photoshop 连接测试")
    print("=" * 60)
    print()

    try:
        # 测试 1: 导入模块
        print("[1] 测试 1: 导入 PSForge 模块...")
        from psforge.ps_adapter.application import PhotoshopApp
        from psforge.ps_adapter.context import get_context_info

        print("   [OK] 模块导入成功")
        print()

        # 测试 2: 连接 Photoshop
        print("[2] 测试 2: 连接到 Photoshop...")
        ps_app = PhotoshopApp()
        print("   [OK] 成功连接到 Photoshop")
        print()

        # 测试 3: 获取 PS 版本
        print("[3] 测试 3: 获取 Photoshop 版本...")
        version = ps_app.get_photoshop_version()
        print(f"   [OK] Photoshop 版本: {version}")
        print()

        # 测试 4: 检查文档状态
        print("[4] 测试 4: 检查文档状态...")
        has_doc = ps_app.has_active_document()
        if has_doc:
            print("   [OK] 当前有打开的文档")
        else:
            print("   [INFO] 当前没有打开的文档（这是正常的）")
        print()

        # 测试 5: 获取上下文信息
        print("[5] 测试 5: 获取上下文信息...")
        context = get_context_info()

        if "error" not in context:
            print("   [OK] 成功获取上下文信息")
            print(f"   - 有文档: {context.get('has_document', False)}")

            if context.get("has_document"):
                doc = context.get("document", {})
                print(f"   - 文档名称: {doc.get('name', 'N/A')}")
                print(f"   - 文档尺寸: {doc.get('width', 0)}x{doc.get('height', 0)}px")
                print(f"   - 分辨率: {doc.get('resolution', 0)} DPI")
                print(f"   - 颜色模式: {doc.get('color_mode', 'N/A')}")
                print(f"   - 图层数: {doc.get('layer_count', 0)}")

                if context.get("active_layer"):
                    layer = context.get("active_layer")
                    print(f"   - 当前图层: {layer.get('name', 'N/A')}")
                    print(f"   - 图层类型: {layer.get('kind', 'N/A')}")
                    print(f"   - 不透明度: {layer.get('opacity', 0)}%")
        else:
            print(f"   [WARN] 获取上下文时出现错误: {context.get('error')}")
        print()

        # 测试 6: JavaScript 执行测试
        print("[6] 测试 6: JavaScript 执行测试...")
        test_script = """
        (function() {
            return "JavaScript execution works!";
        })();
        """
        result = ps_app.execute_javascript(test_script)
        print(f"   [OK] JavaScript 执行成功: {result}")
        print()

        # 总结
        print("=" * 60)
        print("[OK] 所有测试通过！PSForge 工作正常")
        print("=" * 60)
        print()
        print("下一步：")
        print("1. 查看 QUICKSTART.md 了解如何使用")
        print("2. 运行 'poetry run python check_tools.py' 验证所有工具")
        print("3. 配置 Claude Desktop 开始使用 MCP 集成")
        print()

        return True

    except ImportError as e:
        print(f"[ERROR] 模块导入失败: {e}")
        print()
        print("解决方案：")
        print("  poetry install")
        print("  或")
        print("  pip install -e .")
        return False

    except ConnectionError as e:
        print(f"[ERROR] 连接 Photoshop 失败: {e}")
        print()
        print("解决方案：")
        print("1. 确认 Photoshop 已启动")
        print("2. 检查 Photoshop 首选项中是否启用了远程连接")
        print("3. 尝试重启 Photoshop")
        return False

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        print()
        print(f"错误类型: {type(e).__name__}")
        print(f"错误详情: {e}")
        print()
        print("请查看 psforge_debug.log 获取详细日志")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
