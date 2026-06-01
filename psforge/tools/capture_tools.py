"""Canvas capture tool - screenshot Photoshop canvas for AI visual feedback."""

import base64
import os
import tempfile
from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register capture tools with MCP server."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def capture_canvas(max_width: int = 1920) -> dict[str, Any]:
        """Capture the current canvas as a PNG image for AI visual analysis.

        Exports a flattened copy of the active document as PNG without
        modifying the original document. Optionally scales down for
        faster transfer.

        Args:
            max_width: Maximum width of the output image in pixels (default: 1920).
                      The image is scaled proportionally if the canvas is wider.

        Returns:
            dict: {success, message, image_base64, width, height, format}
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {"success": False, "error": "No active document"}

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "psforge_capture.png")
        temp_path_escaped = temp_path.replace("\\", "\\\\")

        try:
            capture_script = f"""
            (function() {{
                var doc = app.activeDocument;
                var origWidth = parseInt(doc.width);
                var origHeight = parseInt(doc.height);

                // Duplicate, flatten, and optionally resize
                var tempDoc = doc.duplicate("__psforge_capture__");
                tempDoc.flatten();

                var maxW = {max_width};
                if (origWidth > maxW) {{
                    var ratio = maxW / origWidth;
                    var newH = Math.round(origHeight * ratio);
                    tempDoc.resizeImage(maxW, newH, null, ResampleMethod.BICUBIC);
                }}

                var finalW = parseInt(tempDoc.width);
                var finalH = parseInt(tempDoc.height);

                // Save as PNG
                var saveFile = new File("{temp_path_escaped}");
                var pngOpts = new PNGSaveOptions();
                pngOpts.compression = 6;
                pngOpts.interlaced = false;
                tempDoc.saveAs(saveFile, pngOpts, true, Extension.LOWERCASE);
                tempDoc.close(SaveOptions.DONOTSAVECHANGES);

                return JSON.stringify({{width: finalW, height: finalH}});
            }})();
            """

            import json as json_mod
            result_str = ps_app.execute_javascript(capture_script)
            dims = json_mod.loads(result_str) if isinstance(result_str, str) else result_str

            # Read and encode the PNG
            with open(temp_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Clean up temp file
            try:
                os.remove(temp_path)
            except OSError:
                pass

            return {
                "success": True,
                "message": f"Canvas captured ({dims['width']}x{dims['height']}px)",
                "image_base64": image_data,
                "width": dims["width"],
                "height": dims["height"],
                "format": "png",
            }
        except Exception as e:
            logger.error(f"Failed to capture canvas: {e}")
            # Clean up on error
            try:
                os.remove(temp_path)
            except OSError:
                pass
            return {"success": False, "error": str(e)}

    registered_tools.append(register_tool(mcp, capture_canvas, "capture_canvas"))

    return registered_tools
