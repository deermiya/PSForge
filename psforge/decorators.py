"""MCP tool decorators for logging, debugging, and error handling."""

import functools
import traceback
from typing import Any, Callable

from loguru import logger


def log_tool_call(func: Callable) -> Callable:
    """Log tool call entry and exit with parameters and results.

    Args:
        func: The tool function to wrap.

    Returns:
        Wrapped function with logging.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__
        logger.info(f"Tool called: {tool_name}")
        logger.debug(f"Tool params: args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            if isinstance(result, dict) and "success" in result:
                status = "SUCCESS" if result["success"] else "FAILED"
                logger.info(f"Tool {tool_name} {status}")
            else:
                logger.info(f"Tool {tool_name} completed")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} raised exception: {e}")
            raise

    return wrapper


def debug_tool(func: Callable) -> Callable:
    """Enhanced error handling decorator that ensures consistent error format.

    All errors are caught and converted to standardized dict format:
    {
        "success": False,
        "error": "Brief error message",
        "detailed_error": "Full error with traceback",
        "context": {...}  # Current PS state (if available)
    }

    Args:
        func: The tool function to wrap.

    Returns:
        Wrapped function with enhanced error handling.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict:
        try:
            result = func(*args, **kwargs)
            # If function returns dict with success field, pass through
            if isinstance(result, dict):
                return result
            # Otherwise wrap in success format
            return {"success": True, "result": result}
        except Exception as e:
            error_msg = str(e)
            detailed_error = traceback.format_exc()

            logger.error(f"Tool {func.__name__} failed: {error_msg}")
            logger.debug(f"Full traceback:\n{detailed_error}")

            # Try to get context even on error
            context = None
            try:
                from psforge.ps_adapter.context import get_context_info

                context = get_context_info()
            except Exception as ctx_error:
                logger.debug(f"Could not retrieve context after error: {ctx_error}")

            return {
                "success": False,
                "error": error_msg,
                "detailed_error": detailed_error,
                "context": context,
            }

    return wrapper
