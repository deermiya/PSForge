#=============================================================    
# module name : check_prompts.py                                    
# author      : Chmy                                       
# create time : 2026-06-05
# description : 检查 MCP Server 是否能正确加载并注册 PS Image Analyzer Prompt
#=============================================================    
"""Check prompt registration for PSForge MCP Server."""

import sys
import io
from pathlib import Path

# Fix Windows console encoding for emoji support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_prompts():
    """Discover and print all registered prompts."""
    print("=" * 60)
    print("PSForge - MCP Prompts 注册检查")
    print("=" * 60)
    print()

    try:
        from mcp.server.fastmcp import FastMCP
        from psforge.registry import discover_and_register_prompts

        print("📦 创建 MCP 服务器实例...")
        mcp = FastMCP("PSForge-PromptCheck")
        print("   ✓ MCP 服务器创建成功")
        print()

        print("🔍 发现并注册 Prompts...")
        prompts = discover_and_register_prompts(mcp)
        print(f"   ✓ 成功注册 {len(prompts)} 个 Prompts")
        print()

        print("📋 Prompt 列表:")
        print("-" * 60)
        for name in prompts:
            print(f"  ✓ {name}")
        print("-" * 60)
        print()

        if "ps-image-analyzer" in prompts:
            print("✅ 测试成功：'ps-image-analyzer' 已成功注册！")
            return True
        else:
            print("❌ 测试失败：未能注册 'ps-image-analyzer'")
            return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_prompts()
    sys.exit(0 if success else 1)
