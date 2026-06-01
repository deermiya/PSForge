"""Inspection tools - query Photoshop state without modifying anything."""

import json
from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register inspection tools with MCP server."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def get_session_info() -> dict[str, Any]:
        """Get Photoshop connection status, version, and current document overview.

        Returns:
            dict: {success, ps_version, ps_running, has_document, document, active_layer}
        """
        ps_app = PhotoshopApp()

        try:
            version = ps_app.get_photoshop_version()
            has_doc = ps_app.has_active_document()

            context = None
            if has_doc:
                from psforge.ps_adapter.context import get_context_info
                context = get_context_info()

            return {
                "success": True,
                "ps_version": version,
                "ps_running": True,
                "has_document": has_doc,
                "context": context,
            }
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {
                "success": False,
                "error": str(e),
                "ps_running": False,
            }

    @debug_tool
    @log_tool_call
    def get_layers() -> dict[str, Any]:
        """Get information about all layers in the active document.

        Returns:
            dict: {success, total_layers, layers: [{index, name, kind, visible, opacity, ...}, ...]}
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {"success": False, "error": "No active document"}

        try:
            get_layers_script = """
            (function() {
                var doc = app.activeDocument;
                var layers = [];
                var kindMap = {
                    1:"NORMAL", 2:"TEXT", 3:"SOLIDFILL", 4:"GRADIENTFILL",
                    5:"PATTERNFILL", 17:"SMARTOBJECT"
                };
                function processLayer(layer, idx) {
                    var isBg = false;
                    try { isBg = layer.isBackgroundLayer; } catch(e) {}
                    var b = {left:0, top:0, right:0, bottom:0};
                    try {
                        b = {
                            left: parseInt(layer.bounds[0]),
                            top: parseInt(layer.bounds[1]),
                            right: parseInt(layer.bounds[2]),
                            bottom: parseInt(layer.bounds[3])
                        };
                    } catch(e) {}
                    return {
                        index: idx, name: layer.name,
                        kind: kindMap[layer.kind] || "UNKNOWN",
                        visible: layer.visible,
                        opacity: parseFloat(layer.opacity),
                        blend_mode: layer.blendMode.toString(),
                        locked: layer.allLocked || layer.pixelsLocked,
                        is_background: isBg,
                        bounds: b,
                        width: b.right - b.left,
                        height: b.bottom - b.top
                    };
                }
                for (var i = 0; i < doc.layers.length; i++) {
                    layers.push(processLayer(doc.layers[i], i));
                }
                return JSON.stringify({total_layers: layers.length, layers: layers});
            })();
            """

            result_str = ps_app.execute_javascript(get_layers_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "total_layers": result["total_layers"],
                "layers": result["layers"],
            }
        except Exception as e:
            logger.error(f"Failed to get layers: {e}")
            return {"success": False, "error": str(e)}

    registered_tools.append(register_tool(mcp, get_session_info, "get_session_info"))
    registered_tools.append(register_tool(mcp, get_layers, "get_layers"))

    return registered_tools
