"""Selection tools - select all, rectangle selection, deselect, invert selection."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all selection tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def select_all() -> dict[str, Any]:
        """Select the entire document (all pixels).

        Returns:
            dict: Operation result and context.
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
            select_all_script = """
            var doc = app.activeDocument;
            doc.selection.selectAll();

            var bounds = doc.selection.bounds;
            JSON.stringify({
                width: parseInt(bounds[2]) - parseInt(bounds[0]),
                height: parseInt(bounds[3]) - parseInt(bounds[1])
            });
            """

            import json

            result_str = ps_app.execute_javascript(select_all_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "message": "Selected entire document",
                "selection_width": result["width"],
                "selection_height": result["height"],
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to select all: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def select_rectangle(top: int, left: int, bottom: int, right: int) -> dict[str, Any]:
        """Create a rectangular selection.

        Args:
            top: Top edge position in pixels.
            left: Left edge position in pixels.
            bottom: Bottom edge position in pixels.
            right: Right edge position in pixels.

        Returns:
            dict: Operation result and context.
        """
        # Validate bounds
        if left >= right:
            return {
                "success": False,
                "error": "left must be < right",
                "context": get_context_info(),
            }
        if top >= bottom:
            return {
                "success": False,
                "error": "top must be < bottom",
                "context": get_context_info(),
            }

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            select_rect_script = f"""
            var doc = app.activeDocument;

            // Create selection region
            var selRegion = [
                [{left}, {top}],
                [{right}, {top}],
                [{right}, {bottom}],
                [{left}, {bottom}]
            ];

            doc.selection.select(selRegion);

            "Rectangle selected";
            """

            ps_app.execute_javascript(select_rect_script)

            width = right - left
            height = bottom - top

            return {
                "success": True,
                "message": f"Created rectangular selection ({width}x{height}px)",
                "bounds": {"top": top, "left": left, "bottom": bottom, "right": right},
                "width": width,
                "height": height,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to create rectangle selection: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def deselect() -> dict[str, Any]:
        """Deselect (remove current selection).

        Returns:
            dict: Operation result and context.
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
            deselect_script = """
            app.activeDocument.selection.deselect();
            "Selection removed";
            """

            ps_app.execute_javascript(deselect_script)

            return {
                "success": True,
                "message": "Selection removed",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to deselect: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def invert_selection() -> dict[str, Any]:
        """Invert the current selection (select what was not selected, deselect what was selected).

        Returns:
            dict: Operation result and context.
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
            invert_script = """
            var doc = app.activeDocument;

            // Check if there's a selection
            try {
                var bounds = doc.selection.bounds;
                if (!bounds) {
                    throw new Error("No selection to invert");
                }
            } catch(e) {
                throw new Error("No selection to invert");
            }

            doc.selection.invert();
            "Selection inverted";
            """

            result = ps_app.execute_javascript(invert_script)

            if "No selection" in str(result):
                return {
                    "success": False,
                    "error": "No selection to invert",
                    "context": get_context_info(),
                }

            return {
                "success": True,
                "message": "Selection inverted",
                "context": get_context_info(),
            }

        except Exception as e:
            error_msg = str(e)
            if "no selection" in error_msg.lower():
                return {
                    "success": False,
                    "error": "No selection to invert",
                    "context": get_context_info(),
                }

            logger.error(f"Failed to invert selection: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, select_all, "select_all"))
    registered_tools.append(register_tool(mcp, select_rectangle, "select_rectangle"))
    registered_tools.append(register_tool(mcp, deselect, "deselect"))
    registered_tools.append(register_tool(mcp, invert_selection, "invert_selection"))

    return registered_tools
