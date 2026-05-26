"""Layer management tools - create, delete, duplicate, merge, flatten, rasterize."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import js_escape_string
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all layer management tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def create_layer(name: str = "New Layer") -> dict[str, Any]:
        """Create a new empty layer in the active document.

        Args:
            name: Name for the new layer (default: "New Layer").

        Returns:
            dict: Operation result with new layer info and context.
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
            name_escaped = js_escape_string(name)

            create_layer_script = f"""
            var doc = app.activeDocument;
            var newLayer = doc.artLayers.add();
            newLayer.name = "{name_escaped}";
            newLayer.name;
            """

            layer_name = ps_app.execute_javascript(create_layer_script)

            return {
                "success": True,
                "message": f"Created layer '{layer_name}'",
                "layer_name": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to create layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def delete_layer() -> dict[str, Any]:
        """Delete the currently active layer.

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
            # Get layer name before deleting
            get_name_script = "app.activeDocument.activeLayer.name;"
            layer_name = ps_app.execute_javascript(get_name_script)

            # Check if it's a background layer
            check_bg_script = """
            (function() {
                try {
                    return app.activeDocument.activeLayer.isBackgroundLayer;
                } catch(e) {
                    return false;
                }
            })();
            """
            is_background = ps_app.execute_javascript(check_bg_script)

            if is_background:
                return {
                    "success": False,
                    "error": "Cannot delete background layer. Convert it to a regular layer first.",
                    "context": get_context_info(),
                }

            # Delete the layer
            delete_script = "app.activeDocument.activeLayer.remove();"
            ps_app.execute_javascript(delete_script)

            return {
                "success": True,
                "message": f"Deleted layer '{layer_name}'",
                "deleted_layer": layer_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to delete layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def duplicate_layer(new_name: str = "") -> dict[str, Any]:
        """Duplicate the currently active layer.

        Args:
            new_name: Optional name for the duplicated layer (default: auto-generated).

        Returns:
            dict: Operation result with duplicated layer info and context.
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
            if new_name:
                name_escaped = js_escape_string(new_name)
                duplicate_script = f"""
                var originalLayer = app.activeDocument.activeLayer;
                var duplicatedLayer = originalLayer.duplicate();
                duplicatedLayer.name = "{name_escaped}";
                duplicatedLayer.name;
                """
            else:
                duplicate_script = """
                var originalLayer = app.activeDocument.activeLayer;
                var duplicatedLayer = originalLayer.duplicate();
                duplicatedLayer.name;
                """

            duplicated_name = ps_app.execute_javascript(duplicate_script)

            return {
                "success": True,
                "message": f"Duplicated layer as '{duplicated_name}'",
                "new_layer_name": duplicated_name,
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to duplicate layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def merge_visible_layers() -> dict[str, Any]:
        """Merge all visible layers in the active document.

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
            merge_script = """
            app.activeDocument.mergeVisibleLayers();
            "Visible layers merged";
            """

            ps_app.execute_javascript(merge_script)

            return {
                "success": True,
                "message": "Merged all visible layers",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to merge visible layers: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def flatten_image() -> dict[str, Any]:
        """Flatten the image by merging all layers into a single background layer.

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
            flatten_script = """
            app.activeDocument.flatten();
            "Image flattened";
            """

            ps_app.execute_javascript(flatten_script)

            return {
                "success": True,
                "message": "Image flattened - all layers merged into background",
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to flatten image: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def rasterize_layer() -> dict[str, Any]:
        """Rasterize the currently active layer (converts text/shape/smart object to pixels).

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
            # Get layer info before rasterizing
            layer_info_script = """
            (function() {
                var layer = app.activeDocument.activeLayer;
                return {
                    name: layer.name,
                    kind: layer.kind.toString()
                };
            })();
            """

            import json

            layer_info_str = ps_app.execute_javascript(layer_info_script)
            layer_info = json.loads(layer_info_str) if isinstance(layer_info_str, str) else layer_info_str

            # Rasterize the layer
            rasterize_script = """
            var layer = app.activeDocument.activeLayer;
            layer.rasterize(RasterizeType.ENTIRELAYER);
            "Layer rasterized";
            """

            ps_app.execute_javascript(rasterize_script)

            return {
                "success": True,
                "message": f"Rasterized layer '{layer_info.get('name', 'unknown')}'",
                "layer_name": layer_info.get("name"),
                "previous_kind": layer_info.get("kind"),
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to rasterize layer: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, create_layer, "create_layer"))
    registered_tools.append(register_tool(mcp, delete_layer, "delete_layer"))
    registered_tools.append(register_tool(mcp, duplicate_layer, "duplicate_layer"))
    registered_tools.append(register_tool(mcp, merge_visible_layers, "merge_visible_layers"))
    registered_tools.append(register_tool(mcp, flatten_image, "flatten_image"))
    registered_tools.append(register_tool(mcp, rasterize_layer, "rasterize_layer"))

    return registered_tools
