"""History tools - undo, redo, get history."""

from typing import Any

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.ps_adapter.context import get_context_info
from psforge.ps_adapter.utils import validate_numeric_range
from psforge.registry import register_tool


def register(mcp) -> list[str]:
    """Register all history tools with MCP server.

    Args:
        mcp: MCP server instance.

    Returns:
        List of registered tool names.
    """
    registered_tools = []

    @debug_tool
    @log_tool_call
    def undo(steps: int = 1) -> dict[str, Any]:
        """Undo one or more steps in the history.

        Args:
            steps: Number of steps to undo (default: 1, max: 50).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(steps, 1, 50, "steps")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            # Undo multiple steps
            undo_script = f"""
            var doc = app.activeDocument;
            var stepsToUndo = {steps};
            var actualSteps = 0;

            for (var i = 0; i < stepsToUndo; i++) {{
                try {{
                    doc.activeHistoryState = doc.activeHistoryState.parent;
                    actualSteps++;
                }} catch(e) {{
                    // No more history to undo
                    break;
                }}
            }}

            JSON.stringify({{
                steps_undone: actualSteps,
                current_state: doc.activeHistoryState.name
            }});
            """

            import json

            result_str = ps_app.execute_javascript(undo_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "message": f"Undone {result['steps_undone']} step(s)",
                "steps_undone": result["steps_undone"],
                "current_state": result["current_state"],
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to undo: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def redo(steps: int = 1) -> dict[str, Any]:
        """Redo one or more steps in the history.

        Args:
            steps: Number of steps to redo (default: 1, max: 50).

        Returns:
            dict: Operation result and context.
        """
        validate_numeric_range(steps, 1, 50, "steps")

        ps_app = PhotoshopApp()
        doc = ps_app.get_active_document()

        if not doc:
            return {
                "success": False,
                "error": "No active document",
                "context": get_context_info(),
            }

        try:
            # Note: ExtendScript doesn't have a direct "redo" - we need to navigate forward in history
            redo_script = f"""
            var doc = app.activeDocument;
            var stepsToRedo = {steps};
            var actualSteps = 0;

            // Get all history states
            var historyStates = doc.historyStates;
            var currentIndex = -1;

            // Find current history state index
            for (var i = 0; i < historyStates.length; i++) {{
                if (historyStates[i] === doc.activeHistoryState) {{
                    currentIndex = i;
                    break;
                }}
            }}

            // Move forward in history
            for (var i = 0; i < stepsToRedo; i++) {{
                var nextIndex = currentIndex + i + 1;
                if (nextIndex < historyStates.length) {{
                    doc.activeHistoryState = historyStates[nextIndex];
                    actualSteps++;
                }} else {{
                    break;
                }}
            }}

            JSON.stringify({{
                steps_redone: actualSteps,
                current_state: doc.activeHistoryState.name
            }});
            """

            import json

            result_str = ps_app.execute_javascript(redo_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "message": f"Redone {result['steps_redone']} step(s)",
                "steps_redone": result["steps_redone"],
                "current_state": result["current_state"],
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to redo: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    @debug_tool
    @log_tool_call
    def get_history() -> dict[str, Any]:
        """Get the list of history states for the active document.

        Returns:
            dict: Operation result with history states array and context.
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
            get_history_script = """
            (function() {
                var doc = app.activeDocument;
                var historyStates = doc.historyStates;
                var currentState = doc.activeHistoryState;

                var states = [];
                var currentIndex = -1;

                for (var i = 0; i < historyStates.length; i++) {
                    var state = historyStates[i];

                    if (state === currentState) {
                        currentIndex = i;
                    }

                    states.push({
                        index: i,
                        name: state.name,
                        snapshot: state.snapshot,
                        is_current: (state === currentState)
                    });
                }

                return JSON.stringify({
                    total_states: states.length,
                    current_index: currentIndex,
                    current_state: currentState.name,
                    states: states
                });
            })();
            """

            import json

            result_str = ps_app.execute_javascript(get_history_script)
            result = json.loads(result_str) if isinstance(result_str, str) else result_str

            return {
                "success": True,
                "total_states": result["total_states"],
                "current_index": result["current_index"],
                "current_state": result["current_state"],
                "states": result["states"],
                "context": get_context_info(),
            }

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {
                "success": False,
                "error": str(e),
                "context": get_context_info(),
            }

    # Register all tools
    registered_tools.append(register_tool(mcp, undo, "undo"))
    registered_tools.append(register_tool(mcp, redo, "redo"))
    registered_tools.append(register_tool(mcp, get_history, "get_history"))

    return registered_tools
