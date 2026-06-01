"""Action and script execution tools - play actions, run custom scripts."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.utils import js_escape_string
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all action tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def play_action(action_name: str, action_set: str) -> dict[str, Any]:
        """Execute a Photoshop action from an action set.

        Args:
            action_name: Name of the action to execute.
            action_set: Name of the action set containing the action.

        Returns:
            dict: Operation result and context.
        """
        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document. Some actions require an open document.",
            }

        try:
            # Escape strings for JavaScript
            action_name_escaped = js_escape_string(action_name)
            action_set_escaped = js_escape_string(action_set)

            # Execute action via JavaScript
            action_script = f"""
            (function() {{
                try {{
                    app.doAction("{action_name_escaped}", "{action_set_escaped}");
                    return "Action executed successfully";
                }} catch(e) {{
                    return "Error: " + e.toString();
                }}
            }})();
            """

            result = ps_app.execute_javascript(action_script)

            if isinstance(result, str) and result.startswith("Error:"):
                return {
                    "success": False,
                    "error": result,
                    "action_name": action_name,
                    "action_set": action_set,
                }

            return {
                "success": True,
                "message": f"Executed action '{action_name}' from set '{action_set}'",
                "action_name": action_name,
                "action_set": action_set,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            return {
                "success": False,
                "error": str(e),
                "action_name": action_name,
                "action_set": action_set,
            }

    @debug_tool
    @log_tool_call
    def execute_script(script: str) -> dict[str, Any]:
        """Execute arbitrary ExtendScript/JavaScript code in Photoshop.

        This is a powerful tool that allows executing any valid Photoshop ExtendScript.
        Use with caution - invalid scripts can cause errors or unexpected behavior.

        Args:
            script: JavaScript/ExtendScript code to execute in Photoshop.

        Returns:
            dict: Execution result and context.

        Examples:
            - Simple operation: "app.activeDocument.activeLayer.opacity = 50;"
            - Get info: "app.activeDocument.layers.length"
            - Complex: "(function() { var layer = app.activeDocument.activeLayer; layer.rotate(45); return 'Rotated'; })()"
        """
        ps_app = PhotoshopApp()

        if not script or not script.strip():
            return {
                "success": False,
                "error": "Script cannot be empty",
            }

        try:
            logger.info(f"Executing custom script (length: {len(script)} chars)")
            logger.debug(f"Script content:\n{script}")

            # Execute the script
            result = ps_app.execute_javascript(script)

            # Convert result to string if it's not already
            result_str = str(result) if result is not None else "undefined"

            return {
                "success": True,
                "message": "Script executed successfully",
                "result": result_str,
                "script_length": len(script),
            }

        except Exception as e:
            logger.error(f"Script execution failed: {e}")

            # Try to extract useful error info
            error_msg = str(e)

            return {
                "success": False,
                "error": error_msg,
                "script_preview": script[:200] + ("..." if len(script) > 200 else ""),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, play_action, "play_action"))
    registered_tools.append(register_tool(mcp, execute_script, "execute_script"))

    return registered_tools
