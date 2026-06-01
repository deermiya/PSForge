"""Batch tools - execute multiple JS operations in a single COM round trip."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.utils import js_escape_string
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all batch tools with MCP server."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def execute_batch(scripts: list[str]) -> dict[str, Any]:
        """Execute multiple ExtendScript snippets in a single COM call.

        Each snippet runs sequentially; results are collected into an array.
        If any snippet fails, subsequent snippets still execute and the
        error is captured in the results array.

        Args:
            scripts: List of JavaScript/ExtendScript code strings.

        Returns:
            dict: {success, results: [{index, success, result/error}, ...]}
        """
        if not scripts:
            return {"success": False, "error": "scripts list is empty"}

        ps_app = PhotoshopApp()

        # Build a wrapper script that runs all snippets and collects results
        parts = []
        for i, script in enumerate(scripts):
            parts.append(f"""
            try {{
                var _r{i} = (function(){{ {script} }})();
                _results.push({{index:{i}, success:true, result:String(_r{i})}});
            }} catch(_e{i}) {{
                _results.push({{index:{i}, success:false, error:_e{i}.toString()}});
            }}""")

        wrapper = "(function(){var _results=[];" + "".join(parts) + "return JSON.stringify(_results);})();"

        try:
            raw = ps_app.execute_javascript(wrapper)

            import json
            results = json.loads(raw) if isinstance(raw, str) else raw

            all_ok = all(r.get("success", False) for r in results)
            return {
                "success": all_ok,
                "message": f"Executed {len(scripts)} scripts ({sum(1 for r in results if r.get('success'))} succeeded)",
                "results": results,
            }

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            return {"success": False, "error": str(e)}

    @debug_tool
    @log_tool_call
    def select_layer_by_name(layer_name: str) -> dict[str, Any]:
        """Select (activate) a layer by its name.

        Args:
            layer_name: Name of the layer to activate.

        Returns:
            dict: Operation result.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {"success": False, "error": "No active document"}

        try:
            name_escaped = js_escape_string(layer_name)
            script = f"""
            (function() {{
                var doc = app.activeDocument;
                var found = false;

                function searchLayers(layers) {{
                    for (var i = 0; i < layers.length; i++) {{
                        if (layers[i].name === "{name_escaped}") {{
                            doc.activeLayer = layers[i];
                            return true;
                        }}
                        if (layers[i].typename === "LayerSet") {{
                            if (searchLayers(layers[i].layers)) return true;
                        }}
                    }}
                    return false;
                }}

                found = searchLayers(doc.layers);
                if (!found) throw new Error("Layer not found: {name_escaped}");
                return doc.activeLayer.name;
            }})();
            """

            result = ps_app.execute_javascript(script)
            return {
                "success": True,
                "message": f"Activated layer '{result}'",
                "layer_name": result,
            }

        except Exception as e:
            logger.error(f"Failed to select layer: {e}")
            return {"success": False, "error": str(e)}

    registered_tools.append(register_tool(mcp, execute_batch, "execute_batch"))
    registered_tools.append(register_tool(mcp, select_layer_by_name, "select_layer_by_name"))

    return registered_tools
