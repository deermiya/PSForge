# PSForge

[![Python 版本](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org/downloads/)
[![MCP 版本](https://img.shields.io/badge/MCP-1.27.1%2B-green.svg)](https://modelcontextprotocol.io/)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![平台](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**🎨 基于 MCP 协议的 AI 驱动 Photoshop 自动化工具**

[English](README.md) | [中文](README_ZH.md)

PSForge 是一个全面的 MCP（模型上下文协议）服务器，它连接 AI 助手（如 Claude）与 Adobe Photoshop。通过清晰、架构良好的 Python 接口，提供 **61 个强大工具**，实现完整的 Photoshop 自动化。

> **⚡ 快速开始：** 查看 [QUICKSTART.md](QUICKSTART.md) 了解安装和测试指南

---

## ✨ 核心特性

- 🛠️ **61 个 Photoshop 工具** - 从文档到滤镜的完整自动化
- 🧠 **按需查询上下文** - 需要时获取 PS 状态，常规操作零开销
- ⚡ **批量执行** - 多个操作通过单次 COM 调用完成
- 🔄 **健壮可靠** - 指数退避自动重试、进程监控
- 🏗️ **清晰架构** - 四层设计，自动发现工具
- 🎯 **类型安全** - 完整的类型注解和参数验证
- 📝 **详尽日志** - 调试日志助力问题排查
- 🚀 **易于扩展** - 添加新工具文件即自动注册

## 📋 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.10 - 3.14 | 必需 |
| **操作系统** | Windows | 使用 COM 接口 |
| **Photoshop** | CC 2019+ | 必须运行中 |
| **MCP 客户端** | 任意 | Claude Desktop、Cursor 等 |

## 🚀 快速安装

### 使用 Poetry（推荐）

```bash
# 克隆或下载项目
cd psforge

# 安装依赖
poetry install

# 验证安装
poetry run python check_tools.py
```

### 使用 pip

```bash
cd psforge
pip install -e .
```

## ⚙️ 配置

### Claude Desktop 配置

**步骤 1：** 编辑 `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "psforge": {
      "command": "D:\\你的路径\\PSForge\\start_psforge.bat"
    }
  }
}
```

⚠️ **重要：** 将路径替换为你的实际项目路径！

**步骤 2：** 重启 Claude Desktop

**步骤 3：** 在 Claude 中测试：
```
使用 PSForge 获取 Photoshop 会话信息
```

### Cursor / 其他 MCP 客户端配置

根据你的客户端文档进行配置：
- **命令：** `poetry run psforge`（或全局安装后用 `psforge`）
- **协议：** stdio
- **工作目录：** 你的 psforge 安装路径

参考 [claude_desktop_config.example.json](claude_desktop_config.example.json) 示例。

## 🏗️ 架构设计

```
┌─────────────────────────────────────────┐
│   AI 客户端（Claude / Cursor）          │
│   自然语言命令                          │
└──────────────┬──────────────────────────┘
               │ MCP 协议（stdio）
┌──────────────▼──────────────────────────┐
│   第 1 层：MCP 服务器（FastMCP）        │
│   • 自动发现和注册                      │
│   • server.py + registry.py             │
└──────────────┬──────────────────────────┘
               │ 工具调用
┌──────────────▼──────────────────────────┐
│   第 2 层：工具层（61 个工具）          │
│   • 按功能分为 15 个模块                │
│   • 完整的参数验证                      │
└──────────────┬──────────────────────────┘
               │ PS 操作
┌──────────────▼──────────────────────────┐
│   第 3 层：PS 适配器                    │
│   • 连接管理                            │
│   • 上下文追踪                          │
│   • 进程守护与重试                      │
└──────────────┬──────────────────────────┘
               │ Windows COM / ExtendScript
┌──────────────▼──────────────────────────┐
│   第 4 层：Adobe Photoshop              │
│   • 直接 API 调用                       │
│   • JavaScript 执行                     │
└─────────────────────────────────────────┘
```

## 🛠️ 工具分类（共 61 个）

<details>
<summary><b>📄 文档工具（5 个）</b></summary>

- `create_document` - 创建新文档（完整控制大小、分辨率、颜色模式）
- `open_image` - 打开图片文件为文档
- `save_document` - 保存为 PSD/JPG/PNG，可设置质量
- `close_document` - 关闭文档（可选保存）
- `crop_document` - 裁剪到指定边界

</details>

<details>
<summary><b>📑 图层工具（6 个）</b></summary>

- `create_layer` - 创建新空白图层
- `delete_layer` - 删除当前图层（带安全检查）
- `duplicate_layer` - 复制图层（可选重命名）
- `merge_visible_layers` - 合并所有可见图层
- `flatten_image` - 拼合为单一背景层
- `rasterize_layer` - 栅格化文字/形状/智能对象

</details>

<details>
<summary><b>🎨 图层属性（6 个）</b></summary>

- `set_layer_opacity` - 设置不透明度（0-100%）
- `set_layer_blend_mode` - 设置混合模式（27 种：正常、正片叠底、滤色、叠加等）
- `set_layer_visibility` - 显示/隐藏图层
- `set_layer_locked` - 锁定/解锁图层
- `rename_layer` - 重命名当前图层
- `fill_layer` - 填充纯色（RGB）

</details>

<details>
<summary><b>🔄 图层变换（5 个）</b></summary>

- `move_layer` - 按 X/Y 像素平移
- `scale_layer` - 按百分比缩放（等比或独立宽高）
- `rotate_layer` - 按度数旋转
- `fit_layer_to_document` - 适配或填充画布
- `resize_image` - 调整整个文档大小（5 种重采样方法）

</details>

<details>
<summary><b>📚 图层排序（5 个）</b></summary>

- `move_layer_up` / `move_layer_down` - 上移/下移一层
- `move_layer_to_top` / `move_layer_to_bottom` - 移到顶部/底部
- `move_layer_to_position` - 相对指定图层定位（上方/下方）

</details>

<details>
<summary><b>✍️ 文字工具（5 个）</b></summary>

- `create_text_layer` - 创建文字层（内容、位置、字体、大小、颜色）
- `update_text_content` - 修改文字内容
- `set_text_font` - 设置字体和/或大小
- `set_text_color` - 设置 RGB 颜色
- `set_text_alignment` - 设置对齐方式（左/中/右）

</details>

<details>
<summary><b>🎭 滤镜工具（4 个）</b></summary>

- `apply_gaussian_blur` - 高斯模糊（半径 0.1-250）
- `apply_motion_blur` - 运动模糊（角度 + 距离）
- `apply_sharpen` - USM 锐化（数量/半径/阈值）
- `apply_noise` - 添加杂色（均匀/高斯分布，可单色）

</details>

<details>
<summary><b>🌈 调整工具（6 个）</b></summary>

- `adjust_brightness_contrast` - 亮度（-150 到 150）/对比度（-50 到 100）
- `adjust_hue_saturation` - 色相/饱和度/明度调整
- `auto_levels` - 自动色阶
- `auto_contrast` - 自动对比度
- `desaturate` - 去色（转灰度）
- `invert` - 反相

</details>

<details>
<summary><b>⬜ 选区工具（4 个）</b></summary>

- `select_all` - 全选文档
- `select_rectangle` - 创建矩形选区
- `deselect` - 取消选择
- `invert_selection` - 反选当前选区

</details>

<details>
<summary><b>🖼️ 图像工具（2 个）</b></summary>

- `place_image` - 置入外部图片为新图层
- `get_layers` - 获取所有图层的详细信息

</details>

<details>
<summary><b>🎭 蒙版工具（3 个）</b></summary>

- `create_layer_mask` - 创建显示全部或隐藏全部蒙版
- `apply_layer_mask` - 应用并删除蒙版
- `delete_layer_mask` - 删除蒙版但不应用

</details>

<details>
<summary><b>⏮️ 历史工具（3 个）</b></summary>

- `undo` - 撤销多个步骤（1-50）
- `redo` - 重做多个步骤（1-50）
- `get_history` - 获取所有历史记录状态列表

</details>

<details>
<summary><b>⚡ 动作与脚本工具（2 个）</b></summary>

- `play_action` - 执行 Photoshop 动作
- `execute_script` - 运行任意 ExtendScript/JavaScript

</details>

<details>
<summary><b>ℹ️ 会话工具（3 个）</b></summary>

- `get_session_info` - PS 版本、运行状态、文档数量
- `get_active_document_info` - 当前文档详细信息
- `get_selection_info` - 当前选区边界和尺寸

</details>

<details>
<summary><b>🚀 批量工具（2 个）</b></summary>

- `execute_batch` - 单次 COM 调用执行多个 ExtendScript 脚本
- `select_layer_by_name` - 按名称激活图层（递归搜索图层组）

</details>

## 💡 使用示例

### 示例 1：创建社交媒体横幅

```
你：创建一个 1200x628 的 Instagram 帖子，蓝色背景，居中白色文字"你好 PSForge"

Claude 会执行：
1. create_document(width=1200, height=628, name="Instagram Post")
2. create_layer(name="Background")
3. fill_layer(red=52, green=152, blue=219)  # 漂亮的蓝色
4. create_text_layer(text="你好 PSForge", x=600, y=314, font_size=72, color_r=255, color_g=255, color_b=255)
5. set_text_alignment(alignment="CENTER")
```

### 示例 2：批量应用效果

```
你：对当前图层应用 5 像素高斯模糊并增加 20 亮度

Claude 会执行：
1. apply_gaussian_blur(radius=5)
2. adjust_brightness_contrast(brightness=20, contrast=0)
```

### 示例 3：复杂图层操作

```
你：复制当前图层，下移一层，降低不透明度到 50%，然后应用运动模糊

Claude 会执行：
1. duplicate_layer()
2. move_layer_down()
3. set_layer_opacity(opacity=50)
4. apply_motion_blur(angle=0, radius=20)
```

## 🧪 测试

### 快速连接测试

```bash
# 需要 Photoshop 正在运行
poetry run python test_connection.py
```

**预期输出：**
```
✅ 所有测试通过！PSForge 工作正常
```

### 验证所有工具

```bash
poetry run python check_tools.py
```

**预期输出：**
```
✅ 成功！所有 61 个工具已注册
```

### 运行单元测试

```bash
poetry run pytest tests/unit/
```

### 运行集成测试

```bash
# ⚠️ 警告：这些测试会在 Photoshop 中创建/修改文档
poetry run pytest tests/integration/
```

## 🔧 开发

### 项目结构

```
psforge/
├── psforge/
│   ├── server.py                    # MCP 服务器入口
│   ├── registry.py                  # 自动发现系统
│   ├── decorators.py                # 错误处理和日志
│   ├── app.py                       # 版本和元数据
│   ├── ps_adapter/                  # Photoshop 接口层
│   │   ├── application.py           # 连接单例 + 重试
│   │   ├── context.py               # 按需状态查询
│   │   ├── process_guard.py         # 健康检查与自动重启
│   │   └── utils.py                 # 辅助函数和验证
│   ├── tools/                       # 15 个工具模块（61 个工具）
│   │   ├── session_tools.py
│   │   ├── document_tools.py
│   │   ├── layer_tools.py
│   │   ├── batch_tools.py
│   │   └── ...（还有 11 个）
│   └── resources/
│       └── （资源提供者）
├── tests/
│   ├── unit/                        # 单元测试
│   └── integration/                 # 集成测试
├── test_connection.py               # 快速连接测试
├── check_tools.py                   # 工具注册检查器
├── pyproject.toml                   # 依赖和配置
├── README.md                        # English
├── README_ZH.md                     # 本文件
├── QUICKSTART.md                    # 快速开始指南
├── CHANGELOG.md                     # 版本历史
└── .gitignore                       # Git 忽略规则
```

### 添加自定义工具

PSForge 使用自动发现系统。只需在 `tools/` 目录下添加新的 Python 文件：

**示例：** `psforge/tools/my_custom_tools.py`

```python
from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter import PhotoshopApp
from psforge.registry import register_tool

def register(mcp):
    """此函数会被注册系统自动调用"""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def my_awesome_tool(param: str) -> dict:
        """在 Photoshop 中做一些很棒的事情。
        
        Args:
            param: 参数描述。
            
        Returns:
            dict: 操作结果。
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()
        
        if not doc:
            return {
                "success": False,
                "error": "没有活动文档",
            }
        
        try:
            # 你的实现代码
            result = ps_app.execute_javascript(f'alert("{param}");')
            
            return {
                "success": True,
                "message": f"使用参数执行: {param}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    registered_tools.append(register_tool(mcp, my_awesome_tool, "my_awesome_tool"))
    return registered_tools
```

**就这样！** 工具会在下次服务器启动时自动发现并注册。

### 代码质量

```bash
# 格式化代码（行宽 120）
poetry run ruff format .

# 检查代码
poetry run ruff check .

# 修复可自动修复的问题
poetry run ruff check --fix .
```

## 🐛 故障排除

### 问题："无法连接到 Photoshop"

**解决方案：**
1. 确保 Photoshop 正在运行
2. 检查是否启用了脚本：首选项 → 常规 → 启用远程连接
3. 重启 Photoshop
4. 查看 `psforge_debug.log` 了解详细错误

### 问题："操作超时"

**解决方案：**
- 默认超时时间为 30 秒
- PSForge 会在超时时自动结束并重启 PS
- 检查 Photoshop 是否有对话框打开（应该会自动禁用）
- 验证 PS 是否未冻结或无响应

### 问题：Claude 中看不到工具

**解决方案：**
1. 验证 `claude_desktop_config.json` 路径是否正确
2. 使用绝对路径指向 `start_psforge.bat`（不要用 `~` 或相对路径）
3. 完全重启 Claude Desktop
4. 检查 Claude Desktop 日志：`%APPDATA%\Claude\logs\`

### 问题：导入错误

**解决方案：**
```bash
# 重新安装依赖
poetry install

# 或使用 pip
pip install -e .
```

## 📝 调试日志

PSForge 自动记录日志到工作目录的 `psforge_debug.log`。

**查看日志：**
```bash
# Windows
type psforge_debug.log

# 或用编辑器打开
notepad psforge_debug.log
```

**日志级别：**
- `INFO` - 一般操作流程
- `DEBUG` - 详细执行步骤
- `WARNING` - 非关键问题
- `ERROR` - 失败和异常

## 📄 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎贡献！请确保：

- ✅ 所有函数都有完整的文档字符串（Google 风格）
- ✅ 所有参数和返回值都有完整的类型注解
- ✅ 测试通过：`poetry run pytest`
- ✅ 代码已格式化：`poetry run ruff format .`
- ✅ 代码检查通过：`poetry run ruff check .`
- ✅ 工具返回 `{"success": bool, ...}` 格式（不在返回值中调用 `get_context_info()`）

## 📦 版本历史

### v0.2.0（2026-06-01）

**性能优化：** 移除所有工具返回值中的 `get_context_info()` 自动附加——每次工具调用节省一次 COM 往返。修复 3×3 双重 retry 嵌套，改为单层 tenacity 重试。

**新工具：** `execute_batch`（单次 COM 调用批量执行 JS）、`select_layer_by_name`（递归按名查找图层）。合计：**61 个工具 / 15 个模块**。

**代码清理：** 移除 `ActionManager` 占位类、未使用的 `execute_with_timeout`、`OperationCounter`、`register_tool` 中的冗余 schema 构建代码。

详见 [CHANGELOG.md](CHANGELOG.md)。

### v0.1.0（2024-05-26）

初始版本。59 个工具，四层架构，自动发现注册，上下文感知返回。

**构建工具：**
- [photoshop-python-api](https://github.com/loonghao/photoshop-python-api) - Photoshop Python API
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 规范
- [mcp](https://pypi.org/project/mcp/) - MCP Python SDK

## 📚 文档

- [快速开始指南](QUICKSTART.md) - 5 分钟上手
- [更新日志](CHANGELOG.md) - 版本历史和变更
- [English Documentation](README.md) - 英文文档

## ⭐ Star 历史

如果你觉得 PSForge 有用，请考虑给它一个 star！⭐

---

**用 ❤️ 为 Photoshop 自动化社区打造**
