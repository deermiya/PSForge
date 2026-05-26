"""Image tools - place image, get layers info."""

import os
from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all image tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def place_image(file_path: str, x: float = 0, y: float = 0) -> dict[str, Any]:
        """Place an image file into the current document as a new layer.

        Args:
            file_path: Full path to the image file to place.
            x: Horizontal position offset in pixels (default: 0).
            y: Vertical position offset in pixels (default: 0).

        Returns:
            dict: Operation result with placed layer info and context.
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
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
            # Convert to Windows path format and escape
            file_path_escaped = file_path.replace("\\", "\\\\")

            place_script = f"""
            var doc = app.activeDocument;
            var fileRef = new File("{file_path_escaped}");

            // Place the file
            var placedLayer = doc.artLayers.add();
            doc.activeLayer = placedLayer;

            // Use File.open to place the image
            var idPlc = charIDToTypeID("Plc ");
            var desc = new ActionDescriptor();
            desc.putPath(charIDToTypeID("null"), fileRef);
            desc.putEnumerated(charIDToTypeID("FTcs"), charIDToTypeID("QCSt"), charIDToTypeID("Qcsa"));
            var idOfst = charIDToTypeID("Ofst");
            var offsetDesc = new ActionDescriptor();
            offsetDesc.putUnitDouble(charIDToTypeID("Hrzn"), charIDToTypeID("#Pxl"), {x});
            offsetDesc.putUnitDouble(charIDToTypeID("Vrtc"), charIDToTypeID("#Pxl"), {y});
            desc.putObject(idOfst, idOfst, offsetDesc);
            executeAction(idPlc, desc, DialogModes.NO);

            doc.activeLayer.name;
            """

            layer_name = ps_app.execute_javascript(place_script)

            return {
                "success": True,
                "message": f"Placed image '{os.path.basename(file_path)}' as layer '{layer_name}'",
                "layer_name": layer_name,
                "file_path": file_path,
                "position": {"x": x, "y": y},
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to place image: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def get_layers() -> dict[str, Any]:
        """Get information about all layers in the active document.

        Returns:
            dict: Operation result with layers array and context.
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
            get_layers_script = """
            (function() {
                var doc = app.activeDocument;
                var layers = [];

                var layerKindMap = {
                    1: "NORMAL",
                    2: "TEXT",
                    3: "SOLIDFILL",
                    4: "GRADIENTFILL",
                    5: "PATTERNFILL",
                    17: "SMARTOBJECT"
                };

                function processLayer(layer, index) {
                    var isBackground = false;
                    try {
                        isBackground = layer.isBackgroundLayer;
                    } catch(e) {}

                    var bounds = {left: 0, top: 0, right: 0, bottom: 0};
                    try {
                        bounds = {
                            left: parseInt(layer.bounds[0]),
                            top: parseInt(layer.bounds[1]),
                            right: parseInt(layer.bounds[2]),
                            bottom: parseInt(layer.bounds[3])
                        };
                    } catch(e) {}

                    return {
                        index: index,
                        name: layer.name,
                        kind: layerKindMap[layer.kind] || "UNKNOWN",
                        visible: layer.visible,
                        opacity: parseFloat(layer.opacity),
                        blend_mode: layer.blendMode.toString(),
                        locked: layer.allLocked || layer.pixelsLocked,
                        is_background: isBackground,
                        bounds: bounds,
                        width: bounds.right - bounds.left,
                        height: bounds.bottom - bounds.top
                    };
                }

                // Get all layers
                for (var i = 0; i < doc.layers.length; i++) {
                    layers.push(processLayer(doc.layers[i], i));
                }

                // Add background layer if exists
                try {
                    if (doc.backgroundLayer) {
                        layers.push(processLayer(doc.backgroundLayer, layers.length));
                    }
                } catch(e) {}

                return JSON.stringify({
                    total_layers: layers.length,
                    layers: layers
                });
            })();
            """

            import json

            result_str = ps_app.execute_javascript(get_layers_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "total_layers": result["total_layers"],
                "layers": result["layers"],
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to get layers: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, place_image, "place_image"))
    registered_tools.append(register_tool(mcp, get_layers, "get_layers"))

    return registered_tools
