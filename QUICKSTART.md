# PSForge 快速开始指南

##  前置要求

- [OK] Windows 系统
- [OK] Python 3.10 - 3.14
- [OK] Adobe Photoshop CC 2019 或更新版本
- [OK] Poetry（推荐）或 pip

##  快速安装

### 方法一：使用 Poetry（推荐）

```bash
# 1. 进入项目目录
cd PSForge

# 2. 安装依赖
poetry install

# 3. 验证安装
poetry run psforge --help
```

### 方法二：使用 pip

```bash
# 1. 进入项目目录
cd PSForge

# 2. 创建虚拟环境（可选但推荐）
python -m venv venv
venv\Scripts\activate

# 3. 安装项目
pip install -e .

# 4. 验证安装
psforge --help
```

##  快速测试

### 测试 1：启动 Photoshop 并测试连接

**步骤：**

1. **启动 Photoshop**
   ```
   手动打开 Adobe Photoshop
   ```

2. **运行独立测试脚本**
   ```bash
   # 使用 Poetry
   poetry run python test_connection.py

   # 或使用 Python
   python test_connection.py
   ```

   **预期输出：**
   ```
   [OK] Successfully connected to Photoshop
   [OK] Photoshop version: 24.x.x
   [OK] Context info retrieved
   [OK] All tests passed!
   ```

### 测试 2：通过 Claude Desktop 使用（完整 MCP 集成）

**步骤：**

1. **配置 Claude Desktop**

   编辑配置文件：`%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "psforge": {
         "command": "C:\\path\\to\\PSForge\\start_psforge.bat"
       }
     }
   }
   ```

   [WARN] **注意：** 将 `C:\\path\\to\\PSForge` 改为你自己的实际克隆路径。`start_psforge.bat` 会自动进入它所在的项目目录，因此项目可以放在任意位置。

2. **重启 Claude Desktop**

3. **在 Claude 中测试**

   输入以下提示：
   ```
   请帮我检查 PSForge 是否正常工作。获取 Photoshop 的会话信息。
   ```

   Claude 应该会调用 `get_session_info` 工具并返回 PS 版本等信息。

### 测试 3：创建简单的文档和图层

**在 Claude Desktop 中输入：**

```
使用 PSForge 完成以下操作：
1. 创建一个 800x600 的 RGB 文档，名为 "Test"
2. 创建一个文字图层，内容是 "Hello PSForge"，位置在 (400, 300)
3. 设置文字颜色为红色（255, 0, 0）
4. 保存为 PSD 到 D:\test.psd
```

Claude 会依次调用：
- `create_document`
- `create_text_layer`
- `set_text_color`
- `save_document`

检查 Photoshop 中是否出现了相应的文档和图层。

##  手动测试单个工具

创建一个 Python 脚本 `manual_test.py`：

```python
"""手动测试 PSForge 工具"""
import sys
sys.path.insert(0, 'psforge')

from psforge.tools import session_tools, document_tools

# 注册工具（模拟 MCP）
class MockMCP:
    def tool(self, name, description):
        def decorator(func):
            return func
        return decorator

mcp = MockMCP()

# 注册会话工具
session_tools.register(mcp)

# 测试 1：获取会话信息
print("测试 1: 获取 Photoshop 会话信息")
result = session_tools.get_session_info()
print(f"成功: {result['success']}")
if result['success']:
    print(f"PS 版本: {result['ps_version']}")
    print(f"有文档: {result['has_document']}")
print()

# 注册文档工具
document_tools.register(mcp)

# 测试 2：创建文档
print("测试 2: 创建新文档")
result = document_tools.create_document(
    width=1920,
    height=1080,
    name="PSForge Test"
)
print(f"成功: {result['success']}")
if result['success']:
    print(f"文档名称: {result['document_name']}")
    print(f"上下文: {result['context']['has_document']}")
print()

# 测试 3：获取文档信息
print("测试 3: 获取文档详细信息")
result = session_tools.get_active_document_info()
print(f"成功: {result['success']}")
if result['success']:
    doc = result['document']
    print(f"文档: {doc['name']}")
    print(f"尺寸: {doc['width']}x{doc['height']} @ {doc['resolution']} DPI")
    print(f"颜色模式: {doc['color_mode']}")
print()

print("[OK] 所有手动测试完成！")
```

运行：
```bash
poetry run python manual_test.py
```

##  验证清单

运行以下命令检查所有工具是否正确注册：

```python
"""检查工具注册"""
import sys
sys.path.insert(0, 'psforge')

from psforge.registry import discover_and_register_tools
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PSForge-Test")
tools = discover_and_register_tools(mcp)

print(f"[OK] 总计注册 {len(tools)} 个工具")
print("\n工具列表：")
for i, tool in enumerate(sorted(tools), 1):
    print(f"{i:2d}. {tool}")

expected = 59
if len(tools) == expected:
    print(f"\n[OK] 成功！所有 {expected} 个工具已注册")
else:
    print(f"\n[WARN]  预期 {expected} 个工具，实际注册了 {len(tools)} 个")
```

保存为 `check_tools.py`，运行：
```bash
poetry run python check_tools.py
```

**预期输出：**
```
[OK] 总计注册 59 个工具

工具列表：
 1. adjust_brightness_contrast
 2. adjust_hue_saturation
 3. apply_gaussian_blur
 4. apply_motion_blur
 ... (共 59 个)

[OK] 成功！所有 59 个工具已注册
```

##  常见问题

### 问题 1：无法连接到 Photoshop

**错误：** `Could not connect to Photoshop`

**解决方案：**
1. 确认 Photoshop 已启动
2. 检查是否启用了远程连接（某些版本需要）：
   - Photoshop → 首选项 → 常规 → 启用远程连接
3. 重启 Photoshop

### 问题 2：导入错误

**错误：** `ModuleNotFoundError: No module named 'photoshop'`

**解决方案：**
```bash
# 重新安装依赖
poetry install
# 或
pip install photoshop-python-api
```

### 问题 3：Claude Desktop 找不到 psforge

**错误：** Claude 说"没有可用的工具"

**解决方案：**
1. 检查 `claude_desktop_config.json` 中的路径是否正确
2. 使用绝对路径，不要用 `~` 或相对路径
3. 确保路径中的反斜杠 `\` 没有被转义（JSON 中用 `\\` 或 `/`）
4. 重启 Claude Desktop

### 问题 4：工具执行超时

**错误：** `Operation timed out after 30 seconds`

**解决方案：**
1. Photoshop 可能卡死，尝试手动操作验证
2. 检查 Photoshop 是否弹出了对话框（PSForge 会禁用，但某些情况仍可能出现）
3. 重启 Photoshop

##  调试日志

PSForge 自动生成调试日志：

**日志位置：** `psforge_debug.log`

**查看日志：**
```bash
# Windows
type psforge_debug.log

# 或用编辑器打开
notepad psforge_debug.log
```

**日志内容示例：**
```
2024-05-26 15:30:00 | INFO     | Tool called: get_session_info
2024-05-26 15:30:01 | DEBUG    | Context retrieved: {"has_document": true, ...}
2024-05-26 15:30:01 | INFO     | Tool get_session_info SUCCESS
```

##  下一步

测试通过后，你可以：

1. **探索所有 59 个工具** - 查看 [README.md](README.md) 的工具列表
2. **创建复杂工作流** - 组合多个工具实现自动化
3. **查看源码** - 了解工具实现细节，自定义功能
4. **贡献代码** - 添加新工具或改进现有功能

##  获取帮助

- **文档：** [README.md](README.md)
- **问题报告：** 在项目仓库创建 Issue
- **调试：** 查看 `psforge_debug.log` 日志文件

---

**提示：** 首次使用建议从简单工具开始测试（如 `get_session_info`），确认连接正常后再尝试复杂操作。
