"""Text layer tools - create, update content, font, color, alignment."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.utils import js_escape_string, validate_color_channel
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all text tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def create_text_layer(
        text: str,
        x: float = 100,
        y: float = 100,
        font_size: float = 24,
        color_r: int = 0,
        color_g: int = 0,
        color_b: int = 0,
    ) -> dict[str, Any]:
        """Create a new text layer with specified content and styling.

        Args:
            text: Text content to display.
            x: Horizontal position in pixels (default: 100).
            y: Vertical position in pixels (default: 100).
            font_size: Font size in points (default: 24).
            color_r: Red channel 0-255 (default: 0).
            color_g: Green channel 0-255 (default: 0).
            color_b: Blue channel 0-255 (default: 0).

        Returns:
            dict: Operation result with text layer info and context.
        """
        validate_color_channel(color_r, "color_r")
        validate_color_channel(color_g, "color_g")
        validate_color_channel(color_b, "color_b")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            text_escaped = js_escape_string(text)

            create_text_script = f"""
            var doc = app.activeDocument;

            // Create text layer
            var textLayer = doc.artLayers.add();
            textLayer.kind = LayerKind.TEXT;

            var textItem = textLayer.textItem;
            textItem.contents = "{text_escaped}";
            textItem.position = [{x}, {y}];
            textItem.size = {font_size};

            // Set color
            var textColor = new SolidColor();
            textColor.rgb.red = {color_r};
            textColor.rgb.green = {color_g};
            textColor.rgb.blue = {color_b};
            textItem.color = textColor;

            textLayer.name;
            """

            layer_name = ps_app.execute_javascript(create_text_script)

            return {
                "success": True,
                "message": f"Created text layer '{layer_name}'",
                "layer_name": layer_name,
                "text": text,
                "position": {"x": x, "y": y},
                "font_size": font_size,
                "color": {"r": color_r, "g": color_g, "b": color_b},
            }

        except Exception as e:
            logger.error(f"Failed to create text layer: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def update_text_content(new_text: str) -> dict[str, Any]:
        """Update the text content of the currently active text layer.

        Args:
            new_text: New text content.

        Returns:
            dict: Operation result and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            text_escaped = js_escape_string(new_text)

            update_script = f"""
            var layer = app.activeDocument.activeLayer;

            // Check if it's a text layer
            if (layer.kind !== LayerKind.TEXT) {{
                throw new Error("Active layer is not a text layer");
            }}

            var oldText = layer.textItem.contents;
            layer.textItem.contents = "{text_escaped}";

            JSON.stringify({{
                layer_name: layer.name,
                old_text: oldText,
                new_text: "{text_escaped}"
            }});
            """

            import json

            result_str = ps_app.execute_javascript(update_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "message": f"Updated text in layer '{result['layer_name']}'",
                "layer_name": result["layer_name"],
                "old_text": result["old_text"],
                "new_text": new_text,
            }

        except Exception as e:
            error_msg = str(e)
            if "not a text layer" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Active layer is not a text layer",
                }

            logger.error(f"Failed to update text content: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def set_text_font(font_name: str, font_size: float = None) -> dict[str, Any]:
        """Set the font family and/or size of the currently active text layer.

        Args:
            font_name: Font family name (e.g., "Arial", "Times New Roman").
            font_size: Optional font size in points.

        Returns:
            dict: Operation result and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            font_escaped = js_escape_string(font_name)

            if font_size is not None:
                set_font_script = f"""
                var layer = app.activeDocument.activeLayer;

                if (layer.kind !== LayerKind.TEXT) {{
                    throw new Error("Active layer is not a text layer");
                }}

                layer.textItem.font = "{font_escaped}";
                layer.textItem.size = {font_size};

                layer.name;
                """
            else:
                set_font_script = f"""
                var layer = app.activeDocument.activeLayer;

                if (layer.kind !== LayerKind.TEXT) {{
                    throw new Error("Active layer is not a text layer");
                }}

                layer.textItem.font = "{font_escaped}";

                layer.name;
                """

            layer_name = ps_app.execute_javascript(set_font_script)

            message = f"Set font of layer '{layer_name}' to '{font_name}'"
            if font_size:
                message += f" at {font_size}pt"

            return {
                "success": True,
                "message": message,
                "layer_name": layer_name,
                "font_name": font_name,
                "font_size": font_size,
            }

        except Exception as e:
            error_msg = str(e)
            if "not a text layer" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Active layer is not a text layer",
                }

            logger.error(f"Failed to set text font: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def set_text_color(red: int, green: int, blue: int) -> dict[str, Any]:
        """Set the color of the currently active text layer.

        Args:
            red: Red channel 0-255.
            green: Green channel 0-255.
            blue: Blue channel 0-255.

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
            }

        try:
            set_color_script = f"""
            var layer = app.activeDocument.activeLayer;

            if (layer.kind !== LayerKind.TEXT) {{
                throw new Error("Active layer is not a text layer");
            }}

            var textColor = new SolidColor();
            textColor.rgb.red = {red};
            textColor.rgb.green = {green};
            textColor.rgb.blue = {blue};
            layer.textItem.color = textColor;

            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_color_script)

            return {
                "success": True,
                "message": f"Set color of text layer '{layer_name}' to RGB({red}, {green}, {blue})",
                "layer_name": layer_name,
                "color": {"red": red, "green": green, "blue": blue},
            }

        except Exception as e:
            error_msg = str(e)
            if "not a text layer" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Active layer is not a text layer",
                }

            logger.error(f"Failed to set text color: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def set_text_alignment(alignment: str) -> dict[str, Any]:
        """Set the alignment of the currently active text layer.

        Args:
            alignment: Text alignment - LEFT, CENTER, or RIGHT.

        Returns:
            dict: Operation result and context.
        """
        alignment = alignment.upper()
        valid_alignments = ["LEFT", "CENTER", "RIGHT"]

        if alignment not in valid_alignments:
            return {
                "success": False,
                "error": f"Invalid alignment '{alignment}'. Must be: {', '.join(valid_alignments)}",
            }

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            set_alignment_script = f"""
            var layer = app.activeDocument.activeLayer;

            if (layer.kind !== LayerKind.TEXT) {{
                throw new Error("Active layer is not a text layer");
            }}

            layer.textItem.justification = Justification.{alignment};

            layer.name;
            """

            layer_name = ps_app.execute_javascript(set_alignment_script)

            return {
                "success": True,
                "message": f"Set alignment of text layer '{layer_name}' to {alignment}",
                "layer_name": layer_name,
                "alignment": alignment,
            }

        except Exception as e:
            error_msg = str(e)
            if "not a text layer" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Active layer is not a text layer",
                }

            logger.error(f"Failed to set text alignment: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, create_text_layer, "create_text_layer"))
    registered_tools.append(register_tool(mcp, update_text_content, "update_text_content"))
    registered_tools.append(register_tool(mcp, set_text_font, "set_text_font"))
    registered_tools.append(register_tool(mcp, set_text_color, "set_text_color"))
    registered_tools.append(register_tool(mcp, set_text_alignment, "set_text_alignment"))

    return registered_tools
