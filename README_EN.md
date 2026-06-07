# PSForge

[![Python Version](https://img.shields.io/badge/python-3.10--3.14-blue.svg)](https://www.python.org/downloads/)
[![MCP Version](https://img.shields.io/badge/MCP-1.27.1%2B-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**AI-Powered Photoshop Automation via Model Context Protocol**

[English](README.md) | [中文](README_ZH.md)

PSForge is an MCP server that lets AI assistants control Adobe Photoshop. Instead of wrapping every PS operation in a separate tool, PSForge exposes a small set of high-leverage tools — the AI generates ExtendScript directly and PSForge executes it via COM.

> **Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for setup guide

---

## Why a Small Core Instead of 61 Tools?

The previous version wrapped each PS operation (create layer, set opacity, apply blur…) as an individual MCP tool — 61 in total. In practice, the AI almost exclusively used `execute_script` to send raw ExtendScript, because:

- A single script can do what 10 tool calls would, in one COM round trip
- ExtendScript is more flexible than any fixed parameter set
- The AI is perfectly capable of generating correct ExtendScript

So v0.3.0 strips away the wrappers and keeps only what matters. v0.4.x keeps the minimal core and adds a high-level workflow tool for image-to-layered-PSD recreation.

## Tools

| Tool | Purpose |
|------|---------|
| `execute_script` | Execute any ExtendScript in Photoshop. The primary workhorse. |
| `execute_batch` | Run multiple scripts in a single COM call. Each collects its own result. |
| `get_session_info` | Check PS connection, version, and current document state. |
| `get_layers` | Get all layers with name, kind, opacity, blend mode, bounds. |
| `capture_canvas` | Screenshot the canvas as base64 PNG for AI visual feedback. |
| `recreate_image_as_layered_psd` | Recreate a reference image as a layered PSD and export a PNG preview. Supports `fast` / `balanced` / `source` modes. |

## Prompts

In addition to tools, PSForge exposes prompt templates that guide AI clients in specialized workflows.

| Prompt | Purpose |
|------|---------|
| `ps-image-analyzer` | Instructs the AI client (using its own Vision capabilities) to analyze a design image and output a structured Photoshop reconstruction specification (JSON) that can be directly executed using PSForge tools. |

### Using Prompts
Prompts are registered automatically via FastMCP. In compatible clients (such as Claude Desktop or Cursor in Agent mode):
1. **Claude Desktop**: Select the `ps-image-analyzer` prompt from the Prompts list in the client interface to initiate the reconstruction session.
2. **Cursor / coding agents**: Command the agent naturally (e.g. *"Use the ps-image-analyzer prompt to reconstruct this screenshot"*). The agent will dynamically fetch the prompt via MCP and use it.


## Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10 - 3.14 | Required |
| OS | Windows | Uses COM interface |
| Photoshop | CC 2019+ | Must be running |
| MCP Client | Any | Claude Desktop, Cursor, etc. |

## Installation

```bash
pip install psforge
```

Or from source:

```bash
git clone https://github.com/deermiya/PSForge.git
cd PSForge
pip install -e .
```

## Configuration

### Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "psforge": {
      "command": "psforge"
    }
  }
}
```

If you run from source, use the bundled launcher and replace the path with your actual clone location:

```json
{
  "mcpServers": {
    "psforge": {
      "command": "C:\\path\\to\\PSForge\\start_psforge.bat"
    }
  }
}
```

Restart Claude Desktop. Test with: `Get Photoshop session info using PSForge`

### Codex

See the example file: [codex_config.example.toml](codex_config.example.toml)

Edit the Codex config file:

```text
%USERPROFILE%\.codex\config.toml
```

If you installed PSForge with `pip install psforge`:

```toml
[mcp_servers.psforge]
command = 'psforge'
startup_timeout_sec = 120
```

If you run from source, use the bundled launcher and replace the path with your actual clone location:

```toml
[mcp_servers.psforge]
command = 'C:\path\to\PSForge\start_psforge.bat'
startup_timeout_sec = 120
```

Save the file, restart Codex, then test with: `Use PSForge to get Photoshop session info`.

## Triggering PSForge in an AI Agent

After configuring the MCP server and restarting your client, ask your agent to use PSForge explicitly:

- `Use PSForge to get Photoshop session info.`
- `Use PSForge to recreate this image as a layered PSD.`
- `Call PSForge recreate_image_as_layered_psd to generate a PSD and preview for this poster.`
- `Use PSForge execute_script to create a Photoshop document.`
- `Use PSForge to batch process PNG images in D:\photos.`

PSForge exposes MCP tools such as `execute_script`, `execute_batch`, `get_session_info`, `get_layers`, `capture_canvas`, and `recreate_image_as_layered_psd`. The agent can call these tools directly to control Photoshop without screen recognition, mouse simulation, or Computer Use.

If the agent does not choose PSForge automatically, add this to your prompt:

```text
Please use the PSForge MCP server, not screen-based automation or Computer Use.
```

Compared with screen-based automation, PSForge controls Photoshop directly through ExtendScript/COM, uses almost no vision tokens, runs faster, and is better suited for editable PSD generation and batch automation.

## Architecture

```
AI Client (Claude / Cursor)
        │ MCP Protocol (stdio)
        ▼
MCP Server (FastMCP)          ← server.py + registry.py
        │ Tool & Prompt Calls
        ▼
Core Tools & Prompts          ← tools/ and prompts/
        │ PS Operations
        ▼
PS Adapter                    ← ps_adapter/ (singleton, retry, context)
        │ Windows COM / ExtendScript
        ▼
Adobe Photoshop
```

## Usage Examples

### One-shot poster creation

```
You: Create a 1080x1350 synthwave poster with gradient background,
     sun with stripes, perspective grid, and title "RETROWAVE"

Claude generates a single ExtendScript that:
1. Creates the document
2. Draws multi-stop gradient background
3. Creates sun with stripe cutouts via selection loops
4. Draws perspective grid with math
5. Adds styled text with outer glow
→ All in one execute_script call
```

### Visual feedback loop

```
You: Open my photo and make it look cinematic

Claude:
1. execute_script → open file, apply curves + color grading
2. capture_canvas → screenshot back to AI
3. AI evaluates: "shadows too deep, highlights need warmth"
4. execute_script → adjust curves, add warm photo filter
5. capture_canvas → verify final result
```

### Batch processing

```
You: Apply watermark to all PNGs in D:\photos

Claude:
1. execute_batch → [open file1 + watermark + save, open file2 + ...]
   All in a single COM round trip
```

## Adding Custom Tools

Drop a Python file into `psforge/tools/`. It auto-registers on startup:

```python
from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter import PhotoshopApp
from psforge.registry import register_tool

def register(mcp):
    registered_tools = []

    @debug_tool
    @log_tool_call
    def my_tool(param: str) -> dict:
        """Your tool description."""
        ps_app = PhotoshopApp()
        result = ps_app.execute_javascript(f'/* your script */')
        return {"success": True, "result": str(result)}

    registered_tools.append(register_tool(mcp, my_tool, "my_tool"))
    return registered_tools


## Adding Custom Prompts

Drop a Python file into `psforge/prompts/`. It auto-registers on startup:

```python
from psforge.registry import register_prompt

def register(mcp):
    def my_prompt() -> str:
        """Prompt description."""
        return "Your prompt template content here."

    register_prompt(mcp, my_prompt, name="my-custom-prompt")
    return ["my-custom-prompt"]
```
```

## Troubleshooting

**"Could not connect to Photoshop"** — Ensure PS is running. Check Preferences → General → Enable Remote Connections. See `psforge_debug.log` for details.

**"Operation timed out"** — Check if PS has dialog boxes open. PSForge auto-disables dialogs, but some operations can still block.

**Tools not showing in Claude** — Verify `claude_desktop_config.json` path. Restart Claude Desktop. Check logs at `%APPDATA%\Claude\logs\`.

## Version History

### v0.4.0

Added MCP Prompts support. Introduced `ps-image-analyzer` prompt template for automatic design analysis and Photoshop reconstruction. Added dynamic auto-registration for custom prompts under `psforge/prompts/`.

### v0.4.x

Added `recreate_image_as_layered_psd` for low-token image-to-layered-PSD workflows. The tool creates a hidden reference layer, separated construction layers, editable text layers, and a PNG preview.

### v0.3.0

Simplified from 61 tools to 5 core tools. Added `capture_canvas` for AI visual feedback. The AI generates ExtendScript directly — no more wrapper tools.

### v0.2.0

Performance: removed auto context queries, fixed retry nesting. Added `execute_batch` and `select_layer_by_name`. 61 tools / 15 modules.

### v0.1.0

Initial release. 59 tools, 4-layer architecture.

## License

MIT License - See [LICENSE](LICENSE)

**Built with [photoshop-python-api](https://github.com/loonghao/photoshop-python-api) and [MCP](https://modelcontextprotocol.io/)**
