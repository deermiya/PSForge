# PSForge

[![Python Version](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org/downloads/)
[![MCP Version](https://img.shields.io/badge/MCP-1.27.1%2B-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**🎨 AI-Powered Photoshop Automation via Model Context Protocol**

[English](README.md) | [中文](README_ZH.md)

PSForge is a comprehensive MCP (Model Context Protocol) server that bridges AI assistants like Claude with Adobe Photoshop. It provides **61 powerful tools** for complete Photoshop automation through a clean, well-architected Python interface.

> **⚡ Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for setup and testing guide

---

## ✨ Key Features

- 🛠️ **61 Photoshop Tools** - Complete automation from documents to filters
- 🧠 **Context On-Demand** - Query PS state when needed, zero overhead on normal operations
- ⚡ **Batch Execution** - Run multiple operations in a single COM round trip
- 🔄 **Robust & Reliable** - Auto-retry with exponential backoff, process monitoring
- 🏗️ **Clean Architecture** - Four-layer design with auto-discovery
- 🎯 **Type-Safe** - Full type annotations and parameter validation
- 📝 **Comprehensive Logging** - Debug logs for troubleshooting
- 🚀 **Easy to Extend** - Drop a new tool file, it auto-registers

## 📋 Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Python** | 3.10 - 3.14 | Required |
| **OS** | Windows | Uses COM interface |
| **Photoshop** | CC 2019+ | Must be running |
| **MCP Client** | Any | Claude Desktop, Cursor, etc. |

## 🚀 Quick Installation

### Using pip (Recommended)

```bash
pip install psforge
```

### Using Poetry (Development)

```bash
# Clone or download the project
cd psforge

# Install dependencies
poetry install

# Verify installation
poetry run python check_tools.py
```

### From source

```bash
cd psforge
pip install -e .
```

## ⚙️ Configuration

### For Claude Desktop

**Step 1:** Edit `%APPDATA%\Claude\claude_desktop_config.json`

If installed via pip:
```json
{
  "mcpServers": {
    "psforge": {
      "command": "psforge"
    }
  }
}
```

If running from source:
```json
{
  "mcpServers": {
    "psforge": {
      "command": "D:\\your-path\\PSForge\\start_psforge.bat"
    }
  }
}
```

**Step 2:** Restart Claude Desktop

**Step 3:** Test in Claude:
```
Get Photoshop session info using PSForge
```

### For Cursor / Other MCP Clients

Configure according to your client's documentation:
- **Command:** `poetry run psforge` (or just `psforge` if installed globally)
- **Protocol:** stdio
- **Working Directory:** Your psforge installation path

See [claude_desktop_config.example.json](claude_desktop_config.example.json) for reference.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│   AI Client (Claude / Cursor)           │
│   Natural Language Commands             │
└──────────────┬──────────────────────────┘
               │ MCP Protocol (stdio)
┌──────────────▼──────────────────────────┐
│   Layer 1: MCP Server (FastMCP)         │
│   • Auto-discovery & Registration       │
│   • server.py + registry.py             │
└──────────────┬──────────────────────────┘
               │ Tool Calls
┌──────────────▼──────────────────────────┐
│   Layer 2: Tools (61 tools)             │
│   • 15 modules by functionality         │
│   • Full parameter validation           │
└──────────────┬──────────────────────────┘
               │ PS Operations
┌──────────────▼──────────────────────────┐
│   Layer 3: PS Adapter                   │
│   • Connection Management               │
│   • Context Tracking                    │
│   • Process Guard & Retry               │
└──────────────┬──────────────────────────┘
               │ Windows COM / ExtendScript
┌──────────────▼──────────────────────────┐
│   Layer 4: Adobe Photoshop              │
│   • Direct API Calls                    │
│   • JavaScript Execution                │
└─────────────────────────────────────────┘
```

## 🛠️ Tool Categories (61 Total)

<details>
<summary><b>📄 Document Tools (5)</b></summary>

- `create_document` - Create new document with full control (size, resolution, color mode)
- `open_image` - Open image file as document
- `save_document` - Save as PSD/JPG/PNG with quality settings
- `close_document` - Close with or without saving
- `crop_document` - Crop to specified bounds

</details>

<details>
<summary><b>📑 Layer Tools (6)</b></summary>

- `create_layer` - Create new empty layer
- `delete_layer` - Delete active layer (with safety checks)
- `duplicate_layer` - Duplicate layer with optional rename
- `merge_visible_layers` - Merge all visible layers
- `flatten_image` - Flatten to single background layer
- `rasterize_layer` - Convert text/shape/smart object to pixels

</details>

<details>
<summary><b>🎨 Layer Properties (6)</b></summary>

- `set_layer_opacity` - Opacity 0-100%
- `set_layer_blend_mode` - 27 blend modes (Normal, Multiply, Screen, Overlay, etc.)
- `set_layer_visibility` - Show/hide layer
- `set_layer_locked` - Lock/unlock layer
- `rename_layer` - Rename active layer
- `fill_layer` - Fill with solid RGB color

</details>

<details>
<summary><b>🔄 Layer Transform (5)</b></summary>

- `move_layer` - Translate by X/Y pixels
- `scale_layer` - Scale by percentage (proportional or independent W/H)
- `rotate_layer` - Rotate by degrees
- `fit_layer_to_document` - Fit or fill canvas
- `resize_image` - Resize entire document (5 resample methods)

</details>

<details>
<summary><b>📚 Layer Ordering (5)</b></summary>

- `move_layer_up` / `move_layer_down` - Move one position
- `move_layer_to_top` / `move_layer_to_bottom` - Move to extremes
- `move_layer_to_position` - Position relative to named layer (above/below)

</details>

<details>
<summary><b>✍️ Text Tools (5)</b></summary>

- `create_text_layer` - Create with content, position, font, size, color
- `update_text_content` - Change text content
- `set_text_font` - Set font family and/or size
- `set_text_color` - Set RGB color
- `set_text_alignment` - Left/Center/Right alignment

</details>

<details>
<summary><b>🎭 Filter Tools (4)</b></summary>

- `apply_gaussian_blur` - Gaussian blur (radius 0.1-250)
- `apply_motion_blur` - Motion blur (angle + distance)
- `apply_sharpen` - Unsharp Mask (amount/radius/threshold)
- `apply_noise` - Add noise (Uniform/Gaussian, monochromatic option)

</details>

<details>
<summary><b>🌈 Adjustment Tools (6)</b></summary>

- `adjust_brightness_contrast` - Brightness (-150 to 150) / Contrast (-50 to 100)
- `adjust_hue_saturation` - Hue/Saturation/Lightness adjustments
- `auto_levels` - Automatic levels correction
- `auto_contrast` - Automatic contrast correction
- `desaturate` - Convert to grayscale
- `invert` - Invert colors

</details>

<details>
<summary><b>⬜ Selection Tools (4)</b></summary>

- `select_all` - Select entire document
- `select_rectangle` - Create rectangular selection
- `deselect` - Remove selection
- `invert_selection` - Invert current selection

</details>

<details>
<summary><b>🖼️ Image Tools (2)</b></summary>

- `place_image` - Place external image as new layer
- `get_layers` - Get comprehensive info on all layers

</details>

<details>
<summary><b>🎭 Mask Tools (3)</b></summary>

- `create_layer_mask` - Reveal-all or hide-all mask
- `apply_layer_mask` - Apply and remove mask
- `delete_layer_mask` - Delete mask without applying

</details>

<details>
<summary><b>⏮️ History Tools (3)</b></summary>

- `undo` - Undo multiple steps (1-50)
- `redo` - Redo multiple steps (1-50)
- `get_history` - Get list of all history states

</details>

<details>
<summary><b>⚡ Action & Script Tools (2)</b></summary>

- `play_action` - Execute Photoshop action from action set
- `execute_script` - Run arbitrary ExtendScript/JavaScript

</details>

<details>
<summary><b>ℹ️ Session Tools (3)</b></summary>

- `get_session_info` - PS version, running status, document count
- `get_active_document_info` - Detailed document information
- `get_selection_info` - Current selection bounds and dimensions

</details>

<details>
<summary><b>🚀 Batch Tools (2)</b></summary>

- `execute_batch` - Run multiple ExtendScript snippets in a single COM round trip
- `select_layer_by_name` - Activate a layer by name (recursive search including layer groups)

</details>

## 💡 Usage Examples

### Example 1: Create a Social Media Banner

```
You: Create a 1200x628 Instagram post with a blue background and centered white text saying "Hello PSForge"

Claude will:
1. create_document(width=1200, height=628, name="Instagram Post")
2. create_layer(name="Background")
3. fill_layer(red=52, green=152, blue=219)  # Nice blue
4. create_text_layer(text="Hello PSForge", x=600, y=314, font_size=72, color_r=255, color_g=255, color_b=255)
5. set_text_alignment(alignment="CENTER")
```

### Example 2: Batch Apply Effects

```
You: Apply a 5px Gaussian blur and increase brightness by 20 on the current layer

Claude will:
1. apply_gaussian_blur(radius=5)
2. adjust_brightness_contrast(brightness=20, contrast=0)
```

### Example 3: Complex Layer Manipulation

```
You: Duplicate the current layer, move it down, reduce opacity to 50%, and apply motion blur

Claude will:
1. duplicate_layer()
2. move_layer_down()
3. set_layer_opacity(opacity=50)
4. apply_motion_blur(angle=0, radius=20)
```

## 🧪 Testing

### Quick Connection Test

```bash
# Requires Photoshop to be running
poetry run python test_connection.py
```

**Expected output:**
```
✅ All tests passed! PSForge is working correctly
```

### Verify All Tools

```bash
poetry run python check_tools.py
```

**Expected output:**
```
✅ Success! All 61 tools registered
```

### Run Unit Tests

```bash
poetry run pytest tests/unit/
```

### Run Integration Tests

```bash
# ⚠️ Warning: These tests will create/modify documents in Photoshop
poetry run pytest tests/integration/
```

## 🔧 Development

### Project Structure

```
psforge/
├── psforge/
│   ├── server.py                    # MCP server entry point
│   ├── registry.py                  # Auto-discovery system
│   ├── decorators.py                # Error handling & logging
│   ├── app.py                       # Version and metadata
│   ├── ps_adapter/                  # Photoshop interface layer
│   │   ├── application.py           # Connection singleton + retry
│   │   ├── context.py               # On-demand state querying
│   │   ├── process_guard.py         # Health check & auto-restart
│   │   └── utils.py                 # Helpers & validation
│   ├── tools/                       # 15 tool modules (61 tools)
│   │   ├── session_tools.py
│   │   ├── document_tools.py
│   │   ├── layer_tools.py
│   │   ├── batch_tools.py
│   │   └── ... (11 more)
│   └── resources/
│       └── (resource providers)
├── tests/
│   ├── unit/                        # Unit tests
│   └── integration/                 # Integration tests
├── test_connection.py               # Quick connection test
├── check_tools.py                   # Tool registration checker
├── pyproject.toml                   # Dependencies & config
├── README.md                        # This file
├── README_ZH.md                     # 中文文档
├── QUICKSTART.md                    # Quick start guide
├── CHANGELOG.md                     # Version history
└── .gitignore                       # Git ignore rules
```

### Adding Custom Tools

PSForge uses an auto-discovery system. Just drop a new Python file into `tools/`:

**Example:** `psforge/tools/my_custom_tools.py`

```python
from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter import PhotoshopApp
from psforge.registry import register_tool

def register(mcp):
    """This function is called automatically by the registry."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def my_awesome_tool(param: str) -> dict:
        """Do something awesome in Photoshop.
        
        Args:
            param: Parameter description.
            
        Returns:
            dict: Operation result.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()
        
        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }
        
        try:
            # Your implementation here
            result = ps_app.execute_javascript(f'alert("{param}");')
            
            return {
                "success": True,
                "message": f"Executed with param: {param}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    registered_tools.append(register_tool(mcp, my_awesome_tool, "my_awesome_tool"))
    return registered_tools
```

**That's it!** The tool will be automatically discovered and registered on next server start.

### Code Quality

```bash
# Format code (line-length 120)
poetry run ruff format .

# Lint code
poetry run ruff check .

# Fix auto-fixable issues
poetry run ruff check --fix .
```

## 🐛 Troubleshooting

### Problem: "Could not connect to Photoshop"

**Solutions:**
1. Ensure Photoshop is running
2. Check if scripting is enabled: Preferences → General → Enable Remote Connections
3. Restart Photoshop
4. Check `psforge_debug.log` for detailed errors

### Problem: "Operation timed out"

**Solutions:**
- Default timeout is 30 seconds
- PSForge will auto-kill and restart PS on timeout
- Check if Photoshop has dialog boxes open (should be auto-disabled)
- Verify PS isn't frozen or unresponsive

### Problem: Tools not showing in Claude

**Solutions:**
1. Verify `claude_desktop_config.json` path is correct
2. Use absolute path for `start_psforge.bat` (no `~` or relative paths)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs: `%APPDATA%\Claude\logs\`

### Problem: Import errors

**Solutions:**
```bash
# Reinstall dependencies
poetry install

# Or with pip
pip install -e .
```

## 📝 Debug Logging

PSForge automatically logs to `psforge_debug.log` in the working directory.

**View logs:**
```bash
# Windows
type psforge_debug.log

# Or open in editor
notepad psforge_debug.log
```

**Log levels:**
- `INFO` - General operation flow
- `DEBUG` - Detailed execution steps
- `WARNING` - Non-critical issues
- `ERROR` - Failures and exceptions

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please ensure:

- ✅ All functions have complete docstrings (Google style)
- ✅ Full type annotations on all parameters and returns
- ✅ Tests pass: `poetry run pytest`
- ✅ Code formatted: `poetry run ruff format .`
- ✅ Linting passes: `poetry run ruff check .`
- ✅ Tools return `{"success": bool, ...}` format (no `get_context_info()` in tool returns)

**Built with:**
- [photoshop-python-api](https://github.com/loonghao/photoshop-python-api) - Photoshop Python API
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [mcp](https://pypi.org/project/mcp/) - MCP Python SDK

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- [Changelog](CHANGELOG.md) - Version history and changes
- [中文文档](README_ZH.md) - Chinese documentation

## 📦 Version History

### v0.2.0 (2026-06-01)

**Performance:** Removed automatic `get_context_info()` from all tool returns — each tool call now saves one COM round trip. Fixed 3×3 double retry nesting down to single-layer retry.

**New tools:** `execute_batch` (batch JS execution in one COM call), `select_layer_by_name` (recursive layer lookup). Total: **61 tools / 15 modules**.

**Cleanup:** Removed dead code — `ActionManager` placeholder, unused `execute_with_timeout`, `OperationCounter`, and redundant schema building in `register_tool`.

See [CHANGELOG.md](CHANGELOG.md) for full details.

### v0.1.0 (2024-05-26)

Initial release. 59 tools, 4-layer architecture, auto-discovery registration, context-aware returns.

## ⭐ Star History

If you find PSForge useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the Photoshop automation community**
