# Changelog

All notable changes to PSForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-06-05

### Added

- **MCP Prompts Support** — Introduced a dynamic discovery and registration system for Prompts (via `@mcp.prompt()`). Prompts in `psforge/prompts/` are auto-registered on startup.
- **`ps-image-analyzer` Prompt Template** — A built-in Prompt template guiding AI agents to perform visual design analysis and output a PSForge-compatible reconstruction JSON spec.
- **Prompt Registration Framework** — Added `register_prompt` and `discover_and_register_prompts` helpers in `psforge/registry.py` to allow easy extension of MCP prompts.

## [0.3.0] - 2026-06-03

### Changed

- **Refactor Core Tools** — Simplified the MCP server from 61 fine-grained wrapper tools down to **5 core tools** (`execute_script`, `execute_batch`, `get_session_info`, `get_layers`, `capture_canvas`).
- **ExtendScript Execution** — AI agents now generate raw ExtendScript/JavaScript directly to execute in Photoshop, offering maximum flexibility and minimizing COM roundtrip overhead.

### Added

- **`capture_canvas` tool** — Screenshot the active document canvas as base64 PNG, enabling visual feedback loops for AI agents.

## [0.2.0] - 2026-06-01

### Performance

- **Remove per-tool `get_context_info()` overhead** — Previously every tool call automatically appended a full PS state query (extra COM round trip). Now context is on-demand via `get_session_info` / `get_active_document_info`. This halves the number of COM calls for typical workflows.
- **Fix double retry nesting** — `execute_javascript` had both a tenacity decorator (3 attempts) and manual retry logic inside `_execute_javascript_internal` (3 attempts), causing up to 9 retries. Now single-layer retry only via tenacity.

### Added

- **`execute_batch` tool** — Run multiple ExtendScript snippets in a single COM round trip. Each snippet is wrapped in try-catch; results collected into an array. Dramatically reduces latency for multi-step operations.
- **`select_layer_by_name` tool** — Activate a layer by name with recursive search through layer groups. Eliminates the need to manually navigate layer hierarchy.
- New tool module: `batch_tools.py` (2 tools, total now **61 tools across 15 modules**)

### Removed

- Dead schema-building code in `register_tool()` (FastMCP handles introspection)
- `ActionManager` class (unused placeholder, file kept as empty stub)
- `execute_with_timeout` function (defined but never called by any tool)
- `OperationCounter` class and `get_operation_counter()` (unused)

### Changed

- `_execute_javascript_internal` simplified to single-attempt execution
- `process_guard.py` trimmed to only `check_photoshop_alive`, `kill_photoshop_process`, `restart_photoshop`
- Updated custom tool example in README (no more `get_context_info()` in returns)

## [0.1.0] - 2026-05-26

### Added - Initial Release

#### Core Architecture (4 Layers)
- **Layer 1: MCP Server** - Auto-discovery and registration system
- **Layer 2: Tools Layer** - 57 Photoshop automation tools
- **Layer 3: PS Adapter** - Connection management, context tracking, process guard
- **Layer 4: Photoshop COM** - Windows COM interface integration

#### PS Adapter Components
- `application.py` - PhotoshopApp singleton with connection management
- `context.py` - Real-time PS state tracking (documents, layers, selections)
- `process_guard.py` - Timeout protection, process monitoring, auto-restart
- `action_manager.py` - Action Manager / Descriptor API integration
- `utils.py` - Retry decorators, validation helpers, JS escaping

#### Session Tools (3 tools)
- `get_session_info` - Get PS version and session status
- `get_active_document_info` - Get detailed document information
- `get_selection_info` - Get current selection details

#### Document Tools (5 tools)
- `create_document` - Create new documents with full control
- `open_image` - Open image files
- `save_document` - Save as PSD/JPG/PNG with quality control
- `close_document` - Close documents with/without saving
- `crop_document` - Crop to specified bounds

#### Layer Management Tools (6 tools)
- `create_layer` - Create new empty layers
- `delete_layer` - Delete active layer (with background protection)
- `duplicate_layer` - Duplicate layers with optional rename
- `merge_visible_layers` - Merge all visible layers
- `flatten_image` - Flatten all layers to background
- `rasterize_layer` - Rasterize text/shape/smart objects

#### Layer Properties Tools (6 tools)
- `set_layer_opacity` - Set opacity 0-100%
- `set_layer_blend_mode` - Set blend mode (27 modes supported)
- `set_layer_visibility` - Show/hide layers
- `set_layer_locked` - Lock/unlock layers
- `rename_layer` - Rename layers
- `fill_layer` - Fill with solid color

#### Layer Ordering Tools (5 tools)
- `move_layer_up` - Move one position up
- `move_layer_down` - Move one position down
- `move_layer_to_top` - Move to top of stack
- `move_layer_to_bottom` - Move to bottom of stack
- `move_layer_to_position` - Position relative to named layer

#### Layer Transform Tools (5 tools)
- `move_layer` - Translate layer position
- `scale_layer` - Scale by percentage (proportional or independent)
- `rotate_layer` - Rotate by degrees
- `fit_layer_to_document` - Fit or fill canvas
- `resize_image` - Resize entire document (5 resample methods)

#### Text Tools (5 tools)
- `create_text_layer` - Create text with font, size, color, position
- `update_text_content` - Change text content
- `set_text_font` - Set font family and size
- `set_text_color` - Set text color (RGB)
- `set_text_alignment` - Set alignment (LEFT/CENTER/RIGHT)

#### Filter Tools (4 tools)
- `apply_gaussian_blur` - Gaussian blur with radius control
- `apply_motion_blur` - Motion blur with angle and distance
- `apply_sharpen` - USM sharpening with amount/radius/threshold
- `apply_noise` - Add noise (UNIFORM/GAUSSIAN, monochromatic option)

#### Adjustment Tools (6 tools)
- `adjust_brightness_contrast` - Brightness/Contrast adjustment
- `adjust_hue_saturation` - Hue/Saturation/Lightness adjustment
- `auto_levels` - Automatic levels correction
- `auto_contrast` - Automatic contrast correction
- `desaturate` - Convert to grayscale
- `invert` - Invert colors

#### Selection Tools (4 tools)
- `select_all` - Select entire document
- `select_rectangle` - Create rectangular selection
- `deselect` - Remove selection
- `invert_selection` - Invert current selection

#### Image Tools (2 tools)
- `place_image` - Place image file as new layer
- `get_layers` - Get detailed info on all layers

#### Mask Tools (3 tools)
- `create_layer_mask` - Create reveal-all or hide-all mask
- `apply_layer_mask` - Apply and remove mask
- `delete_layer_mask` - Delete mask without applying

#### History Tools (3 tools)
- `undo` - Undo multiple steps
- `redo` - Redo multiple steps
- `get_history` - Get history states list

#### Action & Script Tools (2 tools)
- `play_action` - Execute Photoshop actions
- `execute_script` - Run arbitrary ExtendScript/JavaScript

#### Error Handling & Debugging
- `@debug_tool` decorator - Standardized error format with context
- `@log_tool_call` decorator - Comprehensive logging
- Automatic retry logic for transient failures
- Timeout protection with automatic process recovery
- Context info included in every response for AI decision-making

#### Testing & Documentation
- Quick start guide (QUICKSTART.md)
- Connection test script (test_connection.py)
- Tool registration checker (check_tools.py)
- Unit tests for core components
- Integration test framework
- Comprehensive README with all 57 tools documented
- Example Claude Desktop configuration

#### Developer Experience
- Auto-discovery: Just add a tool file to `tools/` directory
- Type hints throughout codebase
- Clear docstrings on all functions
- Ruff formatting (line-length 120)
- Debug logging to `psforge_debug.log`
- Parameter validation with helpful error messages

### Technical Details

- **Python Support:** 3.10 - 3.14
- **MCP Version:** 1.6.0+
- **photoshop-python-api:** 0.24.0
- **Architecture:** Four-layer clean architecture
- **Protocol:** stdio-based MCP communication
- **Platform:** Windows (COM-based)
- **Photoshop:** CC 2019+

### Known Limitations

- Windows only (uses COM interface)
- Requires Photoshop to be running
- Some filters may have different parameter ranges in different PS versions
- Background layer has restrictions (cannot delete, cannot add masks)

### Future Enhancements (Not in 0.1.0)

- Smart object operations
- Channel operations
- Path/vector tools
- Advanced selection tools (magic wand, quick selection)
- Batch processing
- Scripting templates
- Performance optimizations for large documents

---

## [Unreleased]

### Planned for Future Releases

- Layer group operations
- Color adjustment layers
- Advanced text formatting (character/paragraph styles)
- Layer effects (drop shadow, stroke, etc.)
- Export for web workflows
- Support for macOS via Apple Events

---

[0.1.0]: https://github.com/yourname/psforge/releases/tag/v0.1.0
