"""Utility functions and decorators for PS adapter."""

import functools
from typing import Any, Callable

from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def retry_on_ps_error(max_attempts: int = 3, base_wait: float = 1.0) -> Callable:
    """Retry decorator for Photoshop operations that may fail transiently.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_wait: Base wait time in seconds (exponential backoff).

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @retry(
            retry=retry_if_exception_type((ConnectionError, TimeoutError, RuntimeError)),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_wait, min=base_wait, max=10),
            reraise=True,
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"PS operation {func.__name__} failed, will retry: {e}")
                raise

        return wrapper

    return decorator


def validate_numeric_range(value: float, min_val: float, max_val: float, param_name: str) -> None:
    """Validate that a numeric parameter is within the allowed range.

    Args:
        value: The value to validate.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        param_name: Parameter name for error messages.

    Raises:
        ValueError: If value is out of range.
    """
    if not (min_val <= value <= max_val):
        raise ValueError(f"{param_name} must be between {min_val} and {max_val}, got {value}")


def validate_color_channel(value: int, channel_name: str = "color") -> None:
    """Validate that a color channel value is in valid range (0-255).

    Args:
        value: The color channel value.
        channel_name: Channel name for error messages.

    Raises:
        ValueError: If value is out of range.
    """
    if not (0 <= value <= 255):
        raise ValueError(f"{channel_name} must be between 0 and 255, got {value}")


def js_escape_string(text: str) -> str:
    """Escape a string for safe use in JavaScript/ExtendScript.

    Args:
        text: The string to escape.

    Returns:
        Escaped string safe for JavaScript.
    """
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
