"""Layer transformation tools - move, scale, rotate, fit to canvas, resize."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.utils import validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all layer transformation tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def move_layer(x: float, y: float) -> dict[str, Any]:
        """Move the currently active layer to a specific position.

        Args:
            x: Horizontal position offset in pixels (can be negative).
            y: Vertical position offset in pixels (can be negative).

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
            move_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Translate (move relative)
            layer.translate({x}, {y});

            layerName;
            """

            layer_name = ps_app.execute_javascript(move_script)

            return {
                "success": True,
                "message": f"Moved layer '{layer_name}' by ({x}, {y})px",
                "layer_name": layer_name,
                "offset_x": x,
                "offset_y": y,
            }

        except Exception as e:
            logger.error(f"Failed to move layer: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def scale_layer(width_percent: float, height_percent: float = None) -> dict[str, Any]:
        """Scale the currently active layer by percentage.

        Args:
            width_percent: Width scale percentage (e.g., 100 = original, 50 = half, 200 = double).
            height_percent: Height scale percentage (if None, uses width_percent for proportional scaling).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(width_percent, 0.1, 10000, "width_percent")

        if height_percent is None:
            height_percent = width_percent
        else:
            validate_numeric_range(height_percent, 0.1, 10000, "height_percent")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            scale_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Resize (scale from center)
            layer.resize({width_percent}, {height_percent}, AnchorPosition.MIDDLECENTER);

            layerName;
            """

            layer_name = ps_app.execute_javascript(scale_script)

            return {
                "success": True,
                "message": f"Scaled layer '{layer_name}' to {width_percent}% x {height_percent}%",
                "layer_name": layer_name,
                "width_percent": width_percent,
                "height_percent": height_percent,
            }

        except Exception as e:
            logger.error(f"Failed to scale layer: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def rotate_layer(angle: float) -> dict[str, Any]:
        """Rotate the currently active layer by a specified angle.

        Args:
            angle: Rotation angle in degrees (positive = clockwise, negative = counter-clockwise).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(angle, -360, 360, "angle")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            rotate_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Rotate around center
            layer.rotate({angle}, AnchorPosition.MIDDLECENTER);

            layerName;
            """

            layer_name = ps_app.execute_javascript(rotate_script)

            return {
                "success": True,
                "message": f"Rotated layer '{layer_name}' by {angle} degrees",
                "layer_name": layer_name,
                "angle": angle,
            }

        except Exception as e:
            logger.error(f"Failed to rotate layer: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def fit_layer_to_document(fill_document: bool = False) -> dict[str, Any]:
        """Resize the currently active layer to fit or fill the document canvas.

        Args:
            fill_document: If True, fill entire canvas (may crop layer).
                          If False, fit within canvas (may have margins).

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
            fill_js = "true" if fill_document else "false"

            fit_script = f"""
            var doc = app.activeDocument;
            var layer = doc.activeLayer;
            var layerName = layer.name;

            // Get document dimensions
            var docWidth = doc.width.as('px');
            var docHeight = doc.height.as('px');

            // Get layer bounds
            var bounds = layer.bounds;
            var layerWidth = bounds[2].as('px') - bounds[0].as('px');
            var layerHeight = bounds[3].as('px') - bounds[1].as('px');

            // Calculate scale ratio
            var widthRatio = docWidth / layerWidth * 100;
            var heightRatio = docHeight / layerHeight * 100;

            var scaleRatio;
            if ({fill_js}) {{
                // Fill: use larger ratio to cover entire canvas
                scaleRatio = Math.max(widthRatio, heightRatio);
            }} else {{
                // Fit: use smaller ratio to fit within canvas
                scaleRatio = Math.min(widthRatio, heightRatio);
            }}

            // Apply scale
            layer.resize(scaleRatio, scaleRatio, AnchorPosition.MIDDLECENTER);

            // Center layer
            var newBounds = layer.bounds;
            var offsetX = (docWidth - (newBounds[2].as('px') - newBounds[0].as('px'))) / 2 - newBounds[0].as('px');
            var offsetY = (docHeight - (newBounds[3].as('px') - newBounds[1].as('px'))) / 2 - newBounds[1].as('px');
            layer.translate(offsetX, offsetY);

            layerName;
            """

            layer_name = ps_app.execute_javascript(fit_script)

            mode = "fill" if fill_document else "fit"

            return {
                "success": True,
                "message": f"Layer '{layer_name}' resized to {mode} document canvas",
                "layer_name": layer_name,
                "mode": mode,
            }

        except Exception as e:
            logger.error(f"Failed to fit layer to document: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def resize_image(width: int, height: int, resample_method: str = "BICUBIC") -> dict[str, Any]:
        """Resize the entire image (document and all layers).

        Args:
            width: New width in pixels (1-300000).
            height: New height in pixels (1-300000).
            resample_method: Resampling method - BICUBIC, BILINEAR, NEARESTNEIGHBOR,
                           BICUBICSHARPER, BICUBICSMOOTHER (default: BICUBIC).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(width, 1, 300000, "width")
        validate_numeric_range(height, 1, 300000, "height")

        resample_method = resample_method.upper()
        valid_methods = ["BICUBIC", "BILINEAR", "NEARESTNEIGHBOR", "BICUBICSHARPER", "BICUBICSMOOTHER"]

        if resample_method not in valid_methods:
            return {
                "success": False,
                "error": f"Invalid resample_method '{resample_method}'. Must be one of: {', '.join(valid_methods)}",
            }

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
            }

        try:
            resize_script = f"""
            var doc = app.activeDocument;
            var oldWidth = doc.width.as('px');
            var oldHeight = doc.height.as('px');

            // Resize image
            doc.resizeImage({width}, {height}, null, ResampleMethod.{resample_method});

            "Resized from " + oldWidth + "x" + oldHeight + " to {width}x{height}";
            """

            result = ps_app.execute_javascript(resize_script)

            return {
                "success": True,
                "message": f"Resized image to {width}x{height}px using {resample_method}",
                "new_width": width,
                "new_height": height,
                "resample_method": resample_method,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, move_layer, "move_layer"))
    registered_tools.append(register_tool(mcp, scale_layer, "scale_layer"))
    registered_tools.append(register_tool(mcp, rotate_layer, "rotate_layer"))
    registered_tools.append(register_tool(mcp, fit_layer_to_document, "fit_layer_to_document"))
    registered_tools.append(register_tool(mcp, resize_image, "resize_image"))

    return registered_tools
