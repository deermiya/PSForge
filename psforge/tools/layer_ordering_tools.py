"""Layer ordering tools - move layers up/down/top/bottom, position relative to others."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import js_escape_string
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all layer ordering tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def move_layer_up() -> dict[str, Any]:
        """Move the currently active layer up one position in the layer stack.

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
            move_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            try {
                layer.move(layer.parent.layers[layer.itemIndex - 2], ElementPlacement.PLACEBEFORE);
            } catch(e) {
                throw new Error("Cannot move layer up - already at top or invalid position");
            }

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' up one position",
                "layer_name": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            error_msg = str(e)
            if "already at top" in error_msg.lower() or "invalid position" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Layer is already at the top or cannot be moved",
                    "context": get_context_info(),
                }

            logger.error(f"Failed to move layer up: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def move_layer_down() -> dict[str, Any]:
        """Move the currently active layer down one position in the layer stack.

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
            move_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            try {
                layer.move(layer.parent.layers[layer.itemIndex], ElementPlacement.PLACEAFTER);
            } catch(e) {
                throw new Error("Cannot move layer down - already at bottom or invalid position");
            }

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' down one position",
                "layer_name": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            error_msg = str(e)
            if "already at bottom" in error_msg.lower() or "invalid position" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Layer is already at the bottom or cannot be moved",
                    "context": get_context_info(),
                }

            logger.error(f"Failed to move layer down: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def move_layer_to_top() -> dict[str, Any]:
        """Move the currently active layer to the top of the layer stack.

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
            move_script = """
            var doc = app.activeDocument;
            var layer = doc.activeLayer;
            var layerName = layer.name;

            // Move to top (before first layer)
            layer.move(doc.layers[0], ElementPlacement.PLACEBEFORE);

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' to top",
                "layer_name": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to move layer to top: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def move_layer_to_bottom() -> dict[str, Any]:
        """Move the currently active layer to the bottom of the layer stack (above background if exists).

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
            move_script = """
            var doc = app.activeDocument;
            var layer = doc.activeLayer;
            var layerName = layer.name;

            // Move to bottom (after last layer)
            var targetLayer = doc.layers[doc.layers.length - 1];
            layer.move(targetLayer, ElementPlacement.PLACEAFTER);

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' to bottom",
                "layer_name": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to move layer to bottom: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def move_layer_to_position(target_layer_name: str, position: str = "ABOVE") -> dict[str, Any]:
        """Move the currently active layer relative to a target layer.

        Args:
            target_layer_name: Name of the layer to position relative to.
            position: Position relative to target - "ABOVE" or "BELOW" (default: "ABOVE").

        Returns:
            dict: Operation result and context.
        """
        position = position.upper()
        if position not in ["ABOVE", "BELOW"]:
            return {
                "success": False,
                "error": "position must be 'ABOVE' or 'BELOW'",
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
            target_escaped = js_escape_string(target_layer_name)
            placement = "PLACEBEFORE" if position == "ABOVE" else "PLACEAFTER"

            move_script = f"""
            var doc = app.activeDocument;
            var layer = doc.activeLayer;
            var layerName = layer.name;

            // Find target layer
            var targetLayer = null;
            for (var i = 0; i < doc.layers.length; i++) {{
                if (doc.layers[i].name === "{target_escaped}") {{
                    targetLayer = doc.layers[i];
                    break;
                }}
            }}

            if (!targetLayer) {{
                throw new Error("Target layer not found: {target_escaped}");
            }}

            // Move layer
            layer.move(targetLayer, ElementPlacement.{placement});

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' {position.lower()} '{target_layer_name}'",
                "layer_name": layer_name,
                "target_layer": target_layer_name,
                "position": position,
                "context": get_context_info(),
            }

        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return {
                    "success": False,
                    "error": f"Target layer '{target_layer_name}' not found",
                    "context": get_context_info(),
                }

            logger.error(f"Failed to move layer to position: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, move_layer_up, "move_layer_up"))
    registered_tools.append(register_tool(mcp, move_layer_down, "move_layer_down"))
    registered_tools.append(register_tool(mcp, move_layer_to_top, "move_layer_to_top"))
    registered_tools.append(register_tool(mcp, move_layer_to_bottom, "move_layer_to_bottom"))
    registered_tools.append(register_tool(mcp, move_layer_to_position, "move_layer_to_position"))

    return registered_tools
