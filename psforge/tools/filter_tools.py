"""Filter tools - gaussian blur, motion blur, sharpen, noise."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all filter tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def apply_gaussian_blur(radius: float) -> dict[str, Any]:
        """Apply Gaussian Blur filter to the currently active layer.

        Args:
            radius: Blur radius in pixels (0.1-250).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(radius, 0.1, 250, "radius")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            blur_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Gaussian Blur
            layer.applyGaussianBlur({radius});

            layerName;
            """

            layer_name = ps_app.execute_javascript(blur_script)

            return {
                "success": True,
                "message": f"Applied Gaussian Blur (radius: {radius}px) to layer '{layer_name}'",
                "layer_name": layer_name,
                "filter": "Gaussian Blur",
                "radius": radius,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Gaussian Blur: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def apply_motion_blur(angle: float, radius: int) -> dict[str, Any]:
        """Apply Motion Blur filter to the currently active layer.

        Args:
            angle: Blur angle in degrees (-360 to 360).
            radius: Blur distance in pixels (1-999).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(angle, -360, 360, "angle")
        validate_numeric_range(radius, 1, 999, "radius")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            blur_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Motion Blur
            layer.applyMotionBlur({angle}, {radius});

            layerName;
            """

            layer_name = ps_app.execute_javascript(blur_script)

            return {
                "success": True,
                "message": f"Applied Motion Blur (angle: {angle}°, distance: {radius}px) to layer '{layer_name}'",
                "layer_name": layer_name,
                "filter": "Motion Blur",
                "angle": angle,
                "radius": radius,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Motion Blur: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def apply_sharpen(amount: int, radius: float, threshold: int) -> dict[str, Any]:
        """Apply Unsharp Mask (USM) sharpening filter to the currently active layer.

        Args:
            amount: Sharpening amount percentage (1-500).
            radius: Radius in pixels (0.1-250).
            threshold: Threshold levels (0-255).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(amount, 1, 500, "amount")
        validate_numeric_range(radius, 0.1, 250, "radius")
        validate_numeric_range(threshold, 0, 255, "threshold")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            sharpen_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Unsharp Mask
            layer.applyUnSharpMask({amount}, {radius}, {threshold});

            layerName;
            """

            layer_name = ps_app.execute_javascript(sharpen_script)

            return {
                "success": True,
                "message": f"Applied Unsharp Mask to layer '{layer_name}'",
                "layer_name": layer_name,
                "filter": "Unsharp Mask",
                "amount": amount,
                "radius": radius,
                "threshold": threshold,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Unsharp Mask: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def apply_noise(amount: float, distribution: str = "UNIFORM", monochromatic: bool = False) -> dict[str, Any]:
        """Apply Add Noise filter to the currently active layer.

        Args:
            amount: Noise amount percentage (0.1-400).
            distribution: Noise distribution - UNIFORM or GAUSSIAN (default: UNIFORM).
            monochromatic: If True, apply noise to tones only without changing colors.

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(amount, 0.1, 400, "amount")

        distribution = distribution.upper()
        if distribution not in ["UNIFORM", "GAUSSIAN"]:
            return {
                "success": False,
                "error": "distribution must be 'UNIFORM' or 'GAUSSIAN'",
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
            mono_js = "true" if monochromatic else "false"

            noise_script = f"""
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply Add Noise
            layer.applyAddNoise({amount}, NoiseDistribution.{distribution}, {mono_js});

            layerName;
            """

            layer_name = ps_app.execute_javascript(noise_script)

            return {
                "success": True,
                "message": f"Applied Add Noise ({distribution}, {amount}%) to layer '{layer_name}'",
                "layer_name": layer_name,
                "filter": "Add Noise",
                "amount": amount,
                "distribution": distribution,
                "monochromatic": monochromatic,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to apply Add Noise: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, apply_gaussian_blur, "apply_gaussian_blur"))
    registered_tools.append(register_tool(mcp, apply_motion_blur, "apply_motion_blur"))
    registered_tools.append(register_tool(mcp, apply_sharpen, "apply_sharpen"))
    registered_tools.append(register_tool(mcp, apply_noise, "apply_noise"))

    return registered_tools
