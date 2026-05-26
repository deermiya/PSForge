"""Document management tools - create, open, save, close, crop."""

from typing import Any

from loguru import logger
from photoshop.api._document import Document

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import js_escape_string, validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all document tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def create_document(
        width: int,
        height: int,
        resolution: float = 72.0,
        name: str = "Untitled",
        color_mode: str = "RGB",
    ) -> dict[str, Any]:
        """Create a new Photoshop document.

        Args:
            width: Document width in pixels (1-300000).
            height: Document height in pixels (1-300000).
            resolution: Document resolution in DPI (1-999), default 72.
            name: Document name, default "Untitled".
            color_mode: Color mode - RGB, CMYK, GRAYSCALE, LAB, BITMAP (default: RGB).

        Returns:
            dict: Operation result with document info and context.
        """
        # Validate parameters
        validate_numeric_range(width, 1, 300000, "width")
        validate_numeric_range(height, 1, 300000, "height")
        validate_numeric_range(resolution, 1, 999, "resolution")

        color_mode = color_mode.upper()
        valid_modes = ["RGB", "CMYK", "GRAYSCALE", "LAB", "BITMAP"]
        if color_mode not in valid_modes:
            return {
                "success": False,
                "error": f"Invalid color_mode '{color_mode}'. Must be one of: {', '.join(valid_modes)}",
                "context": get_context_info(),
            }

        ps_app = PhotoshopApp()

        try:
            # Use photoshop-python-api to create document
            from photoshop.api._artlayer import ArtLayer

            # Map color mode string to PS constant
            color_mode_map = {
                "RGB": 4,  # NewDocumentMode.RGB
                "CMYK": 5,  # NewDocumentMode.CMYK
                "GRAYSCALE": 2,  # NewDocumentMode.GRAYSCALE
                "LAB": 9,  # NewDocumentMode.LAB
                "BITMAP": 1,  # NewDocumentMode.BITMAP
            }

            mode_value = color_mode_map.get(color_mode, 4)

            # Create document via JavaScript for better control
            create_script = f"""
            var docRef = app.documents.add({width}, {height}, {resolution}, "{js_escape_string(name)}", NewDocumentMode.{color_mode});
            docRef.name;
            """

            result = ps_app.execute_javascript(create_script)

            return {
                "success": True,
                "message": f"Created document '{name}' ({width}x{height}px, {resolution}dpi, {color_mode})",
                "document_name": name,
                "width": width,
                "height": height,
                "resolution": resolution,
                "color_mode": color_mode,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def open_image(file_path: str) -> dict[str, Any]:
        """Open an image file as a new Photoshop document.

        Args:
            file_path: Full path to the image file to open.

        Returns:
            dict: Operation result with opened document info and context.
        """
        import os

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "context": get_context_info(),
            }

        ps_app = PhotoshopApp()

        try:
            # Convert to Windows path format and escape
            file_path_escaped = file_path.replace("\\", "\\\\")

            open_script = f"""
            var fileRef = new File("{file_path_escaped}");
            var docRef = app.open(fileRef);
            docRef.name;
            """

            doc_name = ps_app.execute_javascript(open_script)

            return {
                "success": True,
                "message": f"Opened image: {doc_name}",
                "file_path": file_path,
                "document_name": doc_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def save_document(
        path: str,
        format: str = "psd",
        quality: int = 10,
    ) -> dict[str, Any]:
        """Save the active document.

        Args:
            path: Full file path where to save (without extension).
            format: File format - psd, jpg, png (default: psd).
            quality: JPEG quality 1-12 (only for jpg), default 10.

        Returns:
            dict: Operation result with save info and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document to save",
                "context": get_context_info(),
            }

        format = format.lower()
        if format not in ["psd", "jpg", "png"]:
            return {
                "success": False,
                "error": f"Invalid format '{format}'. Must be: psd, jpg, or png",
                "context": get_context_info(),
            }

        if format == "jpg":
            validate_numeric_range(quality, 1, 12, "quality")

        try:
            path_escaped = path.replace("\\", "\\\\")

            if format == "psd":
                save_script = f"""
                var saveFile = new File("{path_escaped}.psd");
                var psdOptions = new PhotoshopSaveOptions();
                psdOptions.embedColorProfile = true;
                psdOptions.alphaChannels = true;
                psdOptions.layers = true;
                app.activeDocument.saveAs(saveFile, psdOptions, true);
                "{path_escaped}.psd";
                """

            elif format == "jpg":
                save_script = f"""
                var saveFile = new File("{path_escaped}.jpg");
                var jpgOptions = new JPEGSaveOptions();
                jpgOptions.quality = {quality};
                jpgOptions.embedColorProfile = true;
                app.activeDocument.saveAs(saveFile, jpgOptions, true);
                "{path_escaped}.jpg";
                """

            elif format == "png":
                save_script = f"""
                var saveFile = new File("{path_escaped}.png");
                var pngOptions = new PNGSaveOptions();
                pngOptions.compression = 6;
                pngOptions.interlaced = false;
                app.activeDocument.saveAs(saveFile, pngOptions, true);
                "{path_escaped}.png";
                """

            saved_path = ps_app.execute_javascript(save_script)

            return {
                "success": True,
                "message": f"Document saved as {format.upper()}",
                "saved_path": saved_path,
                "format": format,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def close_document(save: bool = False) -> dict[str, Any]:
        """Close the active document.

        Args:
            save: Whether to save before closing (default: False).

        Returns:
            dict: Operation result and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document to close",
                "context": get_context_info(),
            }

        try:
            save_option = "SaveOptions.SAVECHANGES" if save else "SaveOptions.DONOTSAVECHANGES"

            close_script = f"""
            app.activeDocument.close({save_option});
            "Document closed";
            """

            ps_app.execute_javascript(close_script)

            return {
                "success": True,
                "message": "Document closed" + (" and saved" if save else ""),
                "saved": save,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to close document: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def crop_document(top: int, left: int, bottom: int, right: int) -> dict[str, Any]:
        """Crop the active document to specified bounds.

        Args:
            top: Top edge position in pixels.
            left: Left edge position in pixels.
            bottom: Bottom edge position in pixels.
            right: Right edge position in pixels.

        Returns:
            dict: Operation result and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document to crop",
                "context": get_context_info(),
            }

        # Validate bounds
        if left >= right:
            return {"success": False, "error": "left must be < right", "context": get_context_info()}
        if top >= bottom:
            return {"success": False, "error": "top must be < bottom", "context": get_context_info()}

        try:
            crop_script = f"""
            var bounds = [{left}, {top}, {right}, {bottom}];
            app.activeDocument.crop(bounds);
            "Document cropped";
            """

            ps_app.execute_javascript(crop_script)

            new_width = right - left
            new_height = bottom - top

            return {
                "success": True,
                "message": f"Document cropped to {new_width}x{new_height}px",
                "new_width": new_width,
                "new_height": new_height,
                "bounds": {"top": top, "left": left, "bottom": bottom, "right": right},
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to crop document: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, create_document, "create_document"))
    registered_tools.append(register_tool(mcp, open_image, "open_image"))
    registered_tools.append(register_tool(mcp, save_document, "save_document"))
    registered_tools.append(register_tool(mcp, close_document, "close_document"))
    registered_tools.append(register_tool(mcp, crop_document, "crop_document"))

    return registered_tools
