"""Core script execution tools - the primary interface for PS automation."""

import json
from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register script execution tools with MCP server."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def execute_script(script: str) -> dict[str, Any]:
        """Execute ExtendScript/JavaScript code in Photoshop.

        This is the primary tool for PS automation. Any valid ExtendScript
        can be executed, including Action Descriptor operations.
        Use this for ALL Photoshop operations: creating documents, layers,
        text, shapes, filters, adjustments, selections, masks, etc.

        Args:
            script: JavaScript/ExtendScript code to execute in Photoshop.

        Returns:
            dict: {success, message, result} or {success, error}

        Examples:
            - Create document: "app.documents.add(1920, 1080, 72, 'My Doc');"
            - Set layer opacity: "app.activeDocument.activeLayer.opacity = 50;"
            - Complex: "(function() { var doc = app.activeDocument; ... return 'done'; })()"
        """
        ps_app = PhotoshopApp()

        if not script or not script.strip():
            return {"success": False, "error": "Script cannot be empty"}

        try:
            logger.info(f"Executing script ({len(script)} chars)")
            result = ps_app.execute_javascript(script)
            result_str = str(result) if result is not None else "undefined"

            return {
                "success": True,
                "message": "Script executed successfully",
                "result": result_str,
            }
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {"success": False, "error": str(e)}

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
            dict: {success, message, results: [{index, success, result/error}, ...]}
        """
        if not scripts:
            return {"success": False, "error": "scripts list is empty"}

        ps_app = PhotoshopApp()

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

    registered_tools.append(register_tool(mcp, execute_script, "execute_script"))
    registered_tools.append(register_tool(mcp, execute_batch, "execute_batch"))

    return registered_tools
