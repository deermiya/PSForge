"""Process guard for Photoshop - timeout protection, health checks, and restart."""

import os
import signal
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable

import psutil
from loguru import logger


def check_photoshop_alive() -> bool:
    """Check if Photoshop process is running.

    Returns:
        True if Photoshop.exe is running, False otherwise.
    """
    try:
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and "photoshop.exe" in proc.info["name"].lower():
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to check Photoshop process: {e}")
        return False


def kill_photoshop_process() -> bool:
    """Force kill all Photoshop processes.

    Returns:
        True if any process was killed, False otherwise.
    """
    killed = False

    try:
        for proc in psutil.process_iter(["name", "pid"]):
            if proc.info["name"] and "photoshop.exe" in proc.info["name"].lower():
                logger.warning(f"Force killing Photoshop process (PID: {proc.info['pid']})")
                try:
                    process = psutil.Process(proc.info["pid"])
                    process.kill()
                    killed = True
                except Exception as e:
                    logger.error(f"Failed to kill process {proc.info['pid']}: {e}")

        if killed:
            time.sleep(2)  # Wait for processes to fully terminate

    except Exception as e:
        logger.error(f"Error while killing Photoshop: {e}")

    return killed


def restart_photoshop(photoshop_path: str | None = None) -> bool:
    """Restart Photoshop by killing existing processes and starting a new one.

    Args:
        photoshop_path: Optional path to Photoshop executable.
                       If not provided, attempts to find it automatically.

    Returns:
        True if restart was successful, False otherwise.
    """
    logger.info("Restarting Photoshop...")

    # Kill existing processes
    kill_photoshop_process()

    # Try to start Photoshop
    if photoshop_path is None:
        # Common Photoshop installation paths
        possible_paths = [
            r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
            r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
            r"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe",
            r"C:\Program Files\Adobe\Adobe Photoshop CC 2019\Photoshop.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                photoshop_path = path
                break

    if photoshop_path and os.path.exists(photoshop_path):
        try:
            logger.info(f"Starting Photoshop from: {photoshop_path}")
            subprocess.Popen([photoshop_path], shell=False)

            # Wait for Photoshop to start
            max_wait = 30
            for i in range(max_wait):
                time.sleep(1)
                if check_photoshop_alive():
                    logger.info("Photoshop started successfully")
                    time.sleep(3)  # Additional wait for full initialization
                    return True

            logger.error(f"Photoshop did not start within {max_wait} seconds")
            return False

        except Exception as e:
            logger.error(f"Failed to start Photoshop: {e}")
            return False
    else:
        logger.warning("Could not find Photoshop executable path")
        logger.info("Please start Photoshop manually")
        return False


def execute_with_timeout(func: Callable, timeout_seconds: int = 30, *args: Any, **kwargs: Any) -> Any:
    """Execute a function with timeout protection.

    If the function takes longer than timeout_seconds, it will be interrupted
    and Photoshop will be force-killed.

    Args:
        func: Function to execute.
        timeout_seconds: Timeout in seconds (default: 30).
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        Result from func execution.

    Raises:
        TimeoutError: If function execution exceeds timeout.
    """
    logger.debug(f"Executing {func.__name__} with {timeout_seconds}s timeout")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)

        try:
            result = future.result(timeout=timeout_seconds)
            return result

        except FuturesTimeoutError:
            logger.error(f"Operation {func.__name__} timed out after {timeout_seconds}s")

            # Kill Photoshop on timeout
            logger.warning("Force killing Photoshop due to timeout")
            kill_photoshop_process()

            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds. Photoshop was force-killed.")

        except Exception as e:
            logger.error(f"Operation {func.__name__} failed: {e}")
            raise


class OperationCounter:
    """Track operations and trigger restart after threshold."""

    def __init__(self, max_operations: int = 1000):
        """Initialize operation counter.

        Args:
            max_operations: Maximum operations before recommending restart.
        """
        self.count = 0
        self.max_operations = max_operations

    def increment(self) -> bool:
        """Increment counter and check if restart is recommended.

        Returns:
            True if restart is recommended, False otherwise.
        """
        self.count += 1
        if self.count >= self.max_operations:
            logger.warning(f"Reached {self.count} operations, restart recommended")
            return True
        return False

    def reset(self) -> None:
        """Reset counter (call after restart)."""
        self.count = 0
        logger.info("Operation counter reset")


# Global operation counter instance
_operation_counter = OperationCounter(max_operations=1000)


def get_operation_counter() -> OperationCounter:
    """Get the global operation counter instance.

    Returns:
        Global OperationCounter instance.
    """
    return _operation_counter
