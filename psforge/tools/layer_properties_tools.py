"""Layer properties tools - opacity, blend mode, visibility, locked, rename, fill."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import js_escape_string, validate_color_channel, validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all layer property tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def set_layer_opacity(opacity: float) -> dict[str, Any]:
        """Set the opacity of the currently active layer.

        Args:
            opacity: Opacity value from 0 (transparent) to 100 (opaque).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(opacity, 0, 100, "opacity")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            set_opacity_script = f"""
            var layer = app.activeDocument.activeLayer;
            layer.opacity = {opacity};
            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_opacity_script)

            return {
                "success": True,
                "message": f"Set opacity of layer '{layer_name}' to {opacity}%",
                "layer_name": layer_name,
                "opacity": opacity,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to set layer opacity: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def set_layer_blend_mode(blend_mode: str) -> dict[str, Any]:
        """Set the blend mode of the currently active layer.

        Args:
            blend_mode: Blend mode name (NORMAL, MULTIPLY, SCREEN, OVERLAY, SOFTLIGHT, HARDLIGHT,
                       COLORDODGE, COLORBURN, DARKEN, LIGHTEN, DIFFERENCE, EXCLUSION, HUE,
                       SATURATION, COLOR, LUMINOSITY, etc.).

        Returns:
            dict: Operation result and context.
        """
        blend_mode = blend_mode.upper()

        # Valid blend modes in Photoshop
        valid_modes = [
            "NORMAL",
            "DISSOLVE",
            "DARKEN",
            "MULTIPLY",
            "COLORBURN",
            "LINEARBURN",
            "DARKERCOLOR",
            "LIGHTEN",
            "SCREEN",
            "COLORDODGE",
            "LINEARDODGE",
            "LIGHTERCOLOR",
            "OVERLAY",
            "SOFTLIGHT",
            "HARDLIGHT",
            "VIVIDLIGHT",
            "LINEARLIGHT",
            "PINLIGHT",
            "HARDMIX",
            "DIFFERENCE",
            "EXCLUSION",
            "SUBTRACT",
            "DIVIDE",
            "HUE",
            "SATURATION",
            "COLOR",
            "LUMINOSITY",
        ]

        if blend_mode not in valid_modes:
            return {
                "success": False,
                "error": f"Invalid blend_mode '{blend_mode}'. Must be one of: {', '.join(valid_modes[:10])}...",
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
            set_blend_script = f"""
            var layer = app.activeDocument.activeLayer;
            layer.blendMode = BlendMode.{blend_mode};
            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_blend_script)

            return {
                "success": True,
                "message": f"Set blend mode of layer '{layer_name}' to {blend_mode}",
                "layer_name": layer_name,
                "blend_mode": blend_mode,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to set blend mode: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def set_layer_visibility(visible: bool) -> dict[str, Any]:
        """Set the visibility of the currently active layer.

        Args:
            visible: True to show the layer, False to hide it.

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
            visible_js = "true" if visible else "false"

            set_visibility_script = f"""
            var layer = app.activeDocument.activeLayer;
            layer.visible = {visible_js};
            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_visibility_script)

            return {
                "success": True,
                "message": f"Layer '{layer_name}' is now {'visible' if visible else 'hidden'}",
                "layer_name": layer_name,
                "visible": visible,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to set layer visibility: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def set_layer_locked(locked: bool) -> dict[str, Any]:
        """Lock or unlock the currently active layer.

        Args:
            locked: True to lock the layer, False to unlock it.

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
            locked_js = "true" if locked else "false"

            set_locked_script = f"""
            var layer = app.activeDocument.activeLayer;
            layer.allLocked = {locked_js};
            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_locked_script)

            return {
                "success": True,
                "message": f"Layer '{layer_name}' is now {'locked' if locked else 'unlocked'}",
                "layer_name": layer_name,
                "locked": locked,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to set layer lock: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def rename_layer(new_name: str) -> dict[str, Any]:
        """Rename the currently active layer.

        Args:
            new_name: New name for the layer.

        Returns:
            dict: Operation result and context.
        """
        if not new_name or not new_name.strip():
            return {
                "success": False,
                "error": "new_name cannot be empty",
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
            new_name_escaped = js_escape_string(new_name)

            rename_script = f"""
            var layer = app.activeDocument.activeLayer;
            var oldName = layer.name;
            layer.name = "{new_name_escaped}";
            oldName;
            """

            old_name = ps_app.execute_javascript(rename_script)

            return {
                "success": True,
                "message": f"Renamed layer from '{old_name}' to '{new_name}'",
                "old_name": old_name,
                "new_name": new_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to rename layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def fill_layer(red: int, green: int, blue: int) -> dict[str, Any]:
        """Fill the currently active layer with a solid color.

        Args:
            red: Red channel value (0-255).
            green: Green channel value (0-255).
            blue: Blue channel value (0-255).

        Returns:
            dict: Operation result and context.
        """
        validate_color_channel(red, "red")
        validate_color_channel(green, "green")
        validate_color_channel(blue, "blue")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            fill_script = f"""
            var doc = app.activeDocument;
            var layer = doc.activeLayer;

            // Create solid color object
            var color = new SolidColor();
            color.rgb.red = {red};
            color.rgb.green = {green};
            color.rgb.blue = {blue};

            // Fill layer
            doc.selection.selectAll();
            doc.selection.fill(color);
            doc.selection.deselect();

            layer.name;
            """

            layer_name = ps_app.execute_javascript(fill_script)

            return {
                "success": True,
                "message": f"Filled layer '{layer_name}' with RGB({red}, {green}, {blue})",
                "layer_name": layer_name,
                "color": {"red": red, "green": green, "blue": blue},
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to fill layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, set_layer_opacity, "set_layer_opacity"))
    registered_tools.append(register_tool(mcp, set_layer_blend_mode, "set_layer_blend_mode"))
    registered_tools.append(register_tool(mcp, set_layer_visibility, "set_layer_visibility"))
    registered_tools.append(register_tool(mcp, set_layer_locked, "set_layer_locked"))
    registered_tools.append(register_tool(mcp, rename_layer, "rename_layer"))
    registered_tools.append(register_tool(mcp, fill_layer, "fill_layer"))

    return registered_tools
