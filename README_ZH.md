# PSForge

[![Python 版本](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org/downloads/)
[![MCP 版本](https://img.shields.io/badge/MCP-1.27.1%2B-green.svg)](https://modelcontextprotocol.io/)
[![许可证](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![平台](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**基于 MCP 协议的 AI 驱动 Photoshop 自动化工具**

[English](README.md) | [中文](README_ZH.md)

PSForge 是一个 MCP 服务器，让 AI 助手直接控制 Adobe Photoshop。不再为每个 PS 操作单独封装工具，而是暴露 **5 个核心工具** —— AI 直接生成 ExtendScript，PSForge 通过 COM 执行。

> **快速开始：** 查看 [QUICKSTART.md](QUICKSTART.md) 了解安装指南

---

## 为什么从 61 个工具砍到 5 个？

上一版把每个 PS 操作（创建图层、设透明度、加模糊……）都封装成独立的 MCP 工具，共 61 个。实际使用中，AI 几乎只用 `execute_script` 发送原始 ExtendScript，因为：

- 一段脚本能做 10 个工具调用的事，只需一次 COM 往返
- ExtendScript 比任何固定参数集都灵活
- AI 完全有能力生成正确的 ExtendScript

所以 v0.3.0 去掉了所有包壳工具，只保留真正有用的。

## 工具列表

| 工具 | 用途 |
|------|------|
| `execute_script` | 在 Photoshop 中执行任意 ExtendScript。主力工具。 |
| `execute_batch` | 单次 COM 调用执行多段脚本，各自收集结果。 |
| `get_session_info` | 查询 PS 连接状态、版本、当前文档概况。 |
| `get_layers` | 获取所有图层信息（名称、类型、透明度、混合模式、边界）。 |
| `capture_canvas` | 截图画布返回 base64 PNG，供 AI 视觉反馈。 |

## 提示词模板 (Prompts)

除了基础工具，PSForge 还提供内置的 Prompt 模板，帮助大模型以特定的工作流处理任务。

| 提示词 | 用途 |
|------|---------|
| `ps-image-analyzer` | 指引 AI 客户端（利用客户端自身的 Vision 视觉能力）分析参考图，并生成一套可被 PSForge 完美执行的 Photoshop 结构化重建规格书（JSON）。 |

### 如何使用 Prompts
Prompts 由 FastMCP 自动注册，可在支持 MCP Prompt 协议的客户端中使用：
1. **Claude Desktop**：点击输入框左侧的 Prompts 列表，选择 `ps-image-analyzer`，将规则载入上下文。
2. **Cursor / Agent 助手**：用自然语言命令 AI（如 *“使用 ps-image-analyzer 提示词分析此图片并重建”*），Agent 会自动在后台读取并应用该模板。


## 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10 - 3.14 | 必需 |
| 操作系统 | Windows | 使用 COM 接口 |
| Photoshop | CC 2019+ | 需要运行中 |
| MCP 客户端 | 任意 | Claude Desktop、Cursor 等 |

## 安装

```bash
pip install psforge
```

从源码安装：

```bash
git clone https://github.com/deermiya/PSForge.git
cd PSForge
pip install -e .
```

## 配置

### Claude Desktop

编辑 `%APPDATA%\Claude\claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "psforge": {
      "command": "psforge"
    }
  }
}
```

重启 Claude Desktop，测试：`获取 Photoshop 会话信息`

## 架构

```
AI 客户端 (Claude / Cursor)
        │ MCP 协议 (stdio)
        ▼
MCP Server (FastMCP)          ← server.py + registry.py
        │ 工具 & 提示词调用
        ▼
5 个核心工具 & 1 个提示词        ← tools/ 和 prompts/
        │ PS 操作
        ▼
PS 适配层                     ← ps_adapter/（单例、重试、上下文）
        │ Windows COM / ExtendScript
        ▼
Adobe Photoshop
```

## 使用示例

### 一次性生成海报

```
你：创建一张 1080x1350 的 synthwave 风格海报，渐变背景、
    条纹太阳、透视网格、标题 "RETROWAVE"

Claude 生成一段 ExtendScript：
1. 创建文档
2. 绘制多色标渐变背景
3. 用选区循环创建条纹太阳
4. 用数学绘制透视网格
5. 添加带外发光的标题文字
→ 一次 execute_script 调用完成
```

### 视觉反馈循环

```
你：打开这张照片，调成电影感

Claude：
1. execute_script → 打开文件，应用曲线 + 调色
2. capture_canvas → 截图回传给 AI
3. AI 判断："暗部太深，高光需要暖色"
4. execute_script → 调整曲线，加暖色滤镜
5. capture_canvas → 确认最终效果
```

### 批量处理

```
你：给 D:\photos 下所有 PNG 加水印

Claude：
1. execute_batch → [打开文件1 + 加水印 + 保存, 打开文件2 + ...]
   单次 COM 往返完成
```

## 添加自定义工具

在 `psforge/tools/` 目录下新建 Python 文件，启动时自动注册：

```python
from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter import PhotoshopApp
from psforge.registry import register_tool

def register(mcp):
    registered_tools = []

    @debug_tool
    @log_tool_call
    def my_tool(param: str) -> dict:
        """工具描述。"""
        ps_app = PhotoshopApp()
        result = ps_app.execute_javascript(f'/* 你的脚本 */')
        return {"success": True, "result": str(result)}

    registered_tools.append(register_tool(mcp, my_tool, "my_tool"))
    return registered_tools


## 添加自定义提示词 (Prompts)

在 `psforge/prompts/` 目录下新建 Python 文件，启动时自动注册：

```python
from psforge.registry import register_prompt

def register(mcp):
    def my_prompt() -> str:
        """提示词描述。"""
        return "在此处填写你的提示词模板内容。"

    register_prompt(mcp, my_prompt, name="my-custom-prompt")
    return ["my-custom-prompt"]
```
```

## 常见问题

**"无法连接 Photoshop"** — 确保 PS 正在运行。检查 首选项 → 常规 → 启用远程连接。查看 `psforge_debug.log` 了解详情。

**"操作超时"** — 检查 PS 是否有弹窗。PSForge 会自动禁用对话框，但某些操作仍可能阻塞。

**Claude 中看不到工具** — 检查 `claude_desktop_config.json` 路径是否正确。重启 Claude Desktop。查看日志：`%APPDATA%\Claude\logs\`

## 版本历史

### v0.4.0

新增 MCP Prompts（提示词模板）机制。引入 `ps-image-analyzer` 提示词模板，供 AI 客户端自动进行设计图像分析与 Photoshop 重建。支持在 `psforge/prompts/` 目录下动态扫描与自动注册自定义 Prompt。

### v0.3.0

从 61 个工具精简为 5 个核心工具。新增 `capture_canvas` 支持 AI 视觉反馈。AI 直接生成 ExtendScript，不再需要包壳工具。

### v0.2.0

性能优化：移除自动上下文查询，修复重试嵌套。新增 `execute_batch` 和 `select_layer_by_name`。61 个工具 / 15 个模块。

### v0.1.0

首次发布。59 个工具，四层架构。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

**基于 [photoshop-python-api](https://github.com/loonghao/photoshop-python-api) 和 [MCP](https://modelcontextprotocol.io/) 构建**
