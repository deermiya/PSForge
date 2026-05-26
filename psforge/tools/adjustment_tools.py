"""Adjustment tools - brightness/contrast, hue/saturation, auto-levels, auto-contrast, desaturate, invert."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all adjustment tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def adjust_brightness_contrast(brightness: int, contrast: int) -> dict[str, Any]:
        """Adjust brightness and contrast of the currently active layer.

        Args:
            brightness: Brightness adjustment (-150 to 150, 0 = no change).
            contrast: Contrast adjustment (-50 to 100, 0 = no change).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(brightness, -150, 150, "brightness")
        validate_numeric_range(contrast, -50, 100, "contrast")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            adjust_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Brightness/Contrast
            layer.adjustBrightnessContrast({brightness}, {contrast});

            layerName;
            """

            layer_name = ps_app.execute_javascript(adjust_script)

            return {
                "success": True,
                "message": f"Adjusted brightness ({brightness:+d}) and contrast ({contrast:+d}) on layer '{layer_name}'",
                "layer_name": layer_name,
                "brightness": brightness,
                "contrast": contrast,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to adjust brightness/contrast: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def adjust_hue_saturation(hue: int, saturation: int, lightness: int) -> dict[str, Any]:
        """Adjust hue, saturation, and lightness of the currently active layer.

        Args:
            hue: Hue shift in degrees (-180 to 180, 0 = no change).
            saturation: Saturation adjustment (-100 to 100, 0 = no change).
            lightness: Lightness adjustment (-100 to 100, 0 = no change).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(hue, -180, 180, "hue")
        validate_numeric_range(saturation, -100, 100, "saturation")
        validate_numeric_range(lightness, -100, 100, "lightness")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            adjust_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Hue/Saturation
            layer.adjustColorBalance([0, 0, 0], [0, 0, 0], [0, 0, 0], true);
            layer.adjustHueSaturation({hue}, {saturation}, {lightness});

            layerName;
            """

            layer_name = ps_app.execute_javascript(adjust_script)

            return {
                "success": True,
                "message": f"Adjusted hue/saturation/lightness on layer '{layer_name}'",
                "layer_name": layer_name,
                "hue": hue,
                "saturation": saturation,
                "lightness": lightness,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to adjust hue/saturation: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def auto_levels() -> dict[str, Any]:
        """Apply Auto Levels adjustment to the currently active layer.

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
            auto_levels_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Auto Levels
            layer.autoLevels();

            layerName;
            """

            layer_name = ps_app.execute_javascript(auto_levels_script)

            return {
                "success": True,
                "message": f"Applied Auto Levels to layer '{layer_name}'",
                "layer_name": layer_name,
                "adjustment": "Auto Levels",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Auto Levels: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def auto_contrast() -> dict[str, Any]:
        """Apply Auto Contrast adjustment to the currently active layer.

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
            auto_contrast_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Auto Contrast
            layer.autoContrast();

            layerName;
            """

            layer_name = ps_app.execute_javascript(auto_contrast_script)

            return {
                "success": True,
                "message": f"Applied Auto Contrast to layer '{layer_name}'",
                "layer_name": layer_name,
                "adjustment": "Auto Contrast",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Auto Contrast: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def desaturate() -> dict[str, Any]:
        """Desaturate (convert to grayscale) the currently active layer.

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
            desaturate_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Desaturate
            layer.desaturate();

            layerName;
            """

            layer_name = ps_app.execute_javascript(desaturate_script)

            return {
                "success": True,
                "message": f"Desaturated layer '{layer_name}'",
                "layer_name": layer_name,
                "adjustment": "Desaturate",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to desaturate: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def invert() -> dict[str, Any]:
        """Invert colors of the currently active layer.

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
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Invert
            layer.invert();

            layerName;
            """

            layer_name = ps_app.execute_javascript(invert_script)

            return {
                "success": True,
                "message": f"Inverted colors of layer '{layer_name}'",
                "layer_name": layer_name,
                "adjustment": "Invert",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to invert: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, adjust_brightness_contrast, "adjust_brightness_contrast"))
    registered_tools.append(register_tool(mcp, adjust_hue_saturation, "adjust_hue_saturation"))
    registered_tools.append(register_tool(mcp, auto_levels, "auto_levels"))
    registered_tools.append(register_tool(mcp, auto_contrast, "auto_contrast"))
    registered_tools.append(register_tool(mcp, desaturate, "desaturate"))
    registered_tools.append(register_tool(mcp, invert, "invert"))

    return registered_tools
