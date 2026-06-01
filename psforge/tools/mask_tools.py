"""Mask tools - create, apply, delete layer masks."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all mask tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def create_layer_mask(reveal_all: bool = True) -> dict[str, Any]:
        """Create a layer mask for the currently active layer.

        Args:
            reveal_all: If True, create a reveal-all mask (white, shows everything).
                       If False, create a hide-all mask (black, hides everything).

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
            # Check if layer is background
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
                    "error": "Cannot add mask to background layer. Convert it to a regular layer first.",
                }

            # Create mask using Action Descriptor (more reliable)
            if reveal_all:
                create_mask_script = """
                var layer = app.activeDocument.activeLayer;
                var layerName = layer.name;

                // Add reveal-all mask
                var idMk = charIDToTypeID("Mk  ");
                var desc = new ActionDescriptor();
                var idNw = charIDToTypeID("Nw  ");
                var idChnl = charIDToTypeID("Chnl");
                desc.putClass(idNw, idChnl);
                var idAt = charIDToTypeID("At  ");
                var ref = new ActionReference();
                var idChnl = charIDToTypeID("Chnl");
                var idMsk = charIDToTypeID("Msk ");
                ref.putEnumerated(idChnl, idChnl, idMsk);
                desc.putReference(idAt, ref);
                var idUsng = charIDToTypeID("Usng");
                var idUsrM = charIDToTypeID("UsrM");
                var idRvlA = charIDToTypeID("RvlA");
                desc.putEnumerated(idUsng, idUsrM, idRvlA);
                executeAction(idMk, desc, DialogModes.NO);

                layerName;
                """
            else:
                create_mask_script = """
                var layer = app.activeDocument.activeLayer;
                var layerName = layer.name;

                // Add hide-all mask
                var idMk = charIDToTypeID("Mk  ");
                var desc = new ActionDescriptor();
                var idNw = charIDToTypeID("Nw  ");
                var idChnl = charIDToTypeID("Chnl");
                desc.putClass(idNw, idChnl);
                var idAt = charIDToTypeID("At  ");
                var ref = new ActionReference();
                var idChnl = charIDToTypeID("Chnl");
                var idMsk = charIDToTypeID("Msk ");
                ref.putEnumerated(idChnl, idChnl, idMsk);
                desc.putReference(idAt, ref);
                var idUsng = charIDToTypeID("Usng");
                var idUsrM = charIDToTypeID("UsrM");
                var idHdAl = charIDToTypeID("HdAl");
                desc.putEnumerated(idUsng, idUsrM, idHdAl);
                executeAction(idMk, desc, DialogModes.NO);

                layerName;
                """

            layer_name = ps_app.execute_javascript(create_mask_script)

            mask_type = "reveal-all (white)" if reveal_all else "hide-all (black)"

            return {
                "success": True,
                "message": f"Created {mask_type} mask for layer '{layer_name}'",
                "layer_name": layer_name,
                "mask_type": mask_type,
                "reveal_all": reveal_all,
            }

        except Exception as e:
            logger.error(f"Failed to create layer mask: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def apply_layer_mask() -> dict[str, Any]:
        """Apply (flatten) the layer mask of the currently active layer.

        This permanently applies the mask and removes it.

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
            # Check if layer has a mask
            check_mask_script = """
            (function() {
                var layer = app.activeDocument.activeLayer;
                try {
                    // Try to access the mask
                    var hasMask = layer.layerMaskDensity !== undefined;
                    return hasMask;
                } catch(e) {
                    return false;
                }
            })();
            """

            has_mask = ps_app.execute_javascript(check_mask_script)

            if not has_mask:
                return {
                    "success": False,
                    "error": "Active layer does not have a mask",
                }

            apply_mask_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Apply layer mask using Action Descriptor
            var idAppr = charIDToTypeID("Appr");
            var desc = new ActionDescriptor();
            var idNull = charIDToTypeID("null");
            var ref = new ActionReference();
            var idChnl = charIDToTypeID("Chnl");
            var idMsk = charIDToTypeID("Msk ");
            ref.putEnumerated(idChnl, idChnl, idMsk);
            desc.putReference(idNull, ref);
            executeAction(idAppr, desc, DialogModes.NO);

            layerName;
            """

            layer_name = ps_app.execute_javascript(apply_mask_script)

            return {
                "success": True,
                "message": f"Applied layer mask on layer '{layer_name}'",
                "layer_name": layer_name,
            }

        except Exception as e:
            logger.error(f"Failed to apply layer mask: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @debug_tool
    @log_tool_call
    def delete_layer_mask() -> dict[str, Any]:
        """Delete the layer mask of the currently active layer.

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
            # Check if layer has a mask
            check_mask_script = """
            (function() {
                var layer = app.activeDocument.activeLayer;
                try {
                    var hasMask = layer.layerMaskDensity !== undefined;
                    return hasMask;
                } catch(e) {
                    return false;
                }
            })();
            """

            has_mask = ps_app.execute_javascript(check_mask_script)

            if not has_mask:
                return {
                    "success": False,
                    "error": "Active layer does not have a mask",
                }

            delete_mask_script = """
            var layer = app.activeDocument.activeLayer;
            var layerName = layer.name;

            // Delete layer mask using Action Descriptor
            var idDlt = charIDToTypeID("Dlt ");
            var desc = new ActionDescriptor();
            var idNull = charIDToTypeID("null");
            var ref = new ActionReference();
            var idChnl = charIDToTypeID("Chnl");
            var idMsk = charIDToTypeID("Msk ");
            ref.putEnumerated(idChnl, idChnl, idMsk);
            desc.putReference(idNull, ref);
            executeAction(idDlt, desc, DialogModes.NO);

            layerName;
            """

            layer_name = ps_app.execute_javascript(delete_mask_script)

            return {
                "success": True,
                "message": f"Deleted layer mask from layer '{layer_name}'",
                "layer_name": layer_name,
            }

        except Exception as e:
            logger.error(f"Failed to delete layer mask: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, create_layer_mask, "create_layer_mask"))
    registered_tools.append(register_tool(mcp, apply_layer_mask, "apply_layer_mask"))
    registered_tools.append(register_tool(mcp, delete_layer_mask, "delete_layer_mask"))

    return registered_tools
