"""Session information tools - PS version, document info, selection info."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all session tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def get_session_info() -> dict[str, Any]:
        """Get Photoshop version and session status information.

        Returns:
            dict: Session information including:
                - success: bool
                - ps_version: Photoshop version string
                - ps_running: Whether PS is accessible
                - has_document: Whether any document is open
                - context: Current PS context
        """
        ps_app = PhotoshopApp()

        try:
            version = ps_app.get_photoshop_version()
            has_doc = ps_app.has_active_document()
            context = get_context_info()

            return {
                "success": True,
                "ps_version": version,
                "ps_running": True,
                "has_document": has_doc,
                "context": context,
            }

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {
                "success": False,
                "error": str(e),
                "ps_running": False,
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def get_active_document_info() -> dict[str, Any]:
        """Get detailed information about the currently active document.

        Returns:
            dict: Document information including:
                - success: bool
                - document: Document details (name, dimensions, resolution, etc.)
                - layer_count: Number of layers
                - has_selection: Whether a selection is active
                - context: Current PS context
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            # Get comprehensive document info via JavaScript
            doc_info_script = """
            (function() {
                if (!app.documents.length) return null;

                var doc = app.activeDocument;

                var colorModeMap = {
                    1: "BITMAP",
                    2: "GRAYSCALE",
                    3: "INDEXED",
                    4: "RGB",
                    5: "CMYK",
                    7: "MULTICHANNEL",
                    8: "DUOTONE",
                    9: "LAB"
                };

                var bitDepthMap = {
                    1: 1,
                    8: 8,
                    16: 16,
                    32: 32
                };

                var info = {
                    name: doc.name,
                    path: doc.fullName ? doc.fullName.toString() : null,
                    width: parseInt(doc.width),
                    height: parseInt(doc.height),
                    resolution: parseFloat(doc.resolution),
                    color_mode: colorModeMap[doc.mode] || "UNKNOWN",
                    bit_depth: bitDepthMap[doc.bitsPerChannel] || 8,
                    layer_count: doc.layers.length,
                    has_background_layer: false,
                    has_selection: false,
                    saved: !doc.saved
                };

                // Check for background layer
                try {
                    var bg = doc.backgroundLayer;
                    if (bg) info.has_background_layer = true;
                } catch(e) {}

                // Check for selection
                try {
                    var selBounds = doc.selection.bounds;
                    if (selBounds) info.has_selection = true;
                } catch(e) {}

                return JSON.stringify(info);
            })();
            """

            result = ps_app.execute_javascript(doc_info_script)

            import json

            doc_info = json.loads(result) if isinstance(result, str) else result

            return {
                "success": True,
                "document": doc_info,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def get_selection_info() -> dict[str, Any]:
        """Get information about the current selection (if any).

        Returns:
            dict: Selection information including:
                - success: bool
                - has_selection: Whether a selection exists
                - bounds: Selection bounds {left, top, right, bottom} if exists
                - width: Selection width (if exists)
                - height: Selection height (if exists)
                - context: Current PS context
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            selection_script = """
            (function() {
                if (!app.documents.length) return null;

                var doc = app.activeDocument;
                var result = {
                    has_selection: false,
                    bounds: null,
                    width: 0,
                    height: 0
                };

                try {
                    var bounds = doc.selection.bounds;
                    if (bounds && bounds.length === 4) {
                        result.has_selection = true;
                        result.bounds = {
                            left: parseInt(bounds[0]),
                            top: parseInt(bounds[1]),
                            right: parseInt(bounds[2]),
                            bottom: parseInt(bounds[3])
                        };
                        result.width = result.bounds.right - result.bounds.left;
                        result.height = result.bounds.bottom - result.bounds.top;
                    }
                } catch(e) {
                    // No selection
                }

                return JSON.stringify(result);
            })();
            """

            result = ps_app.execute_javascript(selection_script)

            import json

            selection_info = json.loads(result) if isinstance(result, str) else result

            return {
                "success": True,
                **selection_info,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to get selection info: {e}")
            return {
                "success": False,
                "error": str(e),
                "has_selection": False,
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, get_session_info, "get_session_info"))
    registered_tools.append(register_tool(mcp, get_active_document_info, "get_active_document_info"))
    registered_tools.append(register_tool(mcp, get_selection_info, "get_selection_info"))

    return registered_tools
