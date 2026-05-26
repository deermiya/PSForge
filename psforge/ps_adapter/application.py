"""Photoshop application singleton and connection management."""

import time
from typing import Any

from loguru import logger
from photoshop import Session

from psforge.ps_adapter.action_manager import ActionManager
from psforge.ps_adapter.utils import retry_on_ps_error


class PhotoshopApp:
    """Singleton class for managing Photoshop application connection."""

    _instance = None
    _session = None
    _app = None
    _action_manager = None
    _operation_count = 0
    _max_operations_before_restart = 1000  # Restart PS every N operations to prevent memory leaks

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Photoshop connection."""
        if self._app is None:
            self._connect()

    def _connect(self) -> None:
        """Establish connection to Photoshop."""
        try:
            logger.info("Connecting to Photoshop...")

            # Create session
            self._session = Session()
            self._session.__enter__()
            self._app = self._session.app

            # Disable all dialogs to prevent blocking
            self._execute_javascript_internal("app.displayDialogs = DialogModes.NO;")

            # Initialize Action Manager
            self._action_manager = ActionManager(self)

            logger.info("Successfully connected to Photoshop")

        except Exception as e:
            logger.error(f"Failed to connect to Photoshop: {e}")
            raise ConnectionError(f"Could not connect to Photoshop: {e}")

    def _disconnect(self) -> None:
        """Disconnect from Photoshop."""
        try:
            if self._session:
                self._session.__exit__(None, None, None)
                self._session = None
                self._app = None
                self._action_manager = None
                logger.info("Disconnected from Photoshop")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")

    def reconnect(self) -> None:
        """Reconnect to Photoshop (useful after restart)."""
        logger.info("Reconnecting to Photoshop...")
        self._disconnect()
        time.sleep(2)  # Give PS time to fully start
        self._connect()
        self._operation_count = 0

    @property
    def app(self):
        """Get the Photoshop Application object."""
        if self._app is None:
            self._connect()
        return self._app

    @property
    def action_manager(self) -> ActionManager:
        """Get the Action Manager instance."""
        if self._action_manager is None:
            self._action_manager = ActionManager(self)
        return self._action_manager

    def _execute_javascript_internal(self, script: str, retry_count: int = 0) -> Any:
        """Internal JavaScript execution without retry wrapper.

        Args:
            script: JavaScript/ExtendScript code to execute.
            retry_count: Current retry attempt number.

        Returns:
            Result from JavaScript execution.
        """
        max_retries = 3

        try:
            if self._app is None:
                self._connect()

            result = self._app.doJavaScript(script)
            return result

        except Exception as e:
            error_msg = str(e).lower()

            # Check if error is retryable
            is_retryable = any(
                keyword in error_msg
                for keyword in ["timeout", "busy", "not available", "connection", "rpc server", "com object"]
            )

            if is_retryable and retry_count < max_retries:
                logger.warning(f"JavaScript execution failed (attempt {retry_count + 1}/{max_retries}): {e}")
                time.sleep(1 * (retry_count + 1))  # Exponential backoff
                return self._execute_javascript_internal(script, retry_count + 1)
            else:
                logger.error(f"JavaScript execution failed after {retry_count + 1} attempts: {e}")
                raise

    @retry_on_ps_error(max_attempts=3, base_wait=1.0)
    def execute_javascript(self, script: str) -> Any:
        """Execute JavaScript/ExtendScript in Photoshop with retry logic.

        Args:
            script: JavaScript/ExtendScript code to execute.

        Returns:
            Result from JavaScript execution.
        """
        # Increment operation counter
        self._operation_count += 1

        # Optional: Auto-restart PS after many operations to prevent memory leaks
        # Uncomment if you experience stability issues
        # if self._operation_count >= self._max_operations_before_restart:
        #     logger.info(f"Reached {self._operation_count} operations, considering restart...")
        #     from psforge.ps_adapter.process_guard import restart_photoshop
        #     restart_photoshop()
        #     self.reconnect()

        return self._execute_javascript_internal(script)

    def get_active_document(self):
        """Get the currently active document.

        Returns:
            Active document object, or None if no document is open.
        """
        try:
            if self.app.documents.length == 0:
                return None
            return self.app.activeDocument
        except Exception as e:
            logger.error(f"Failed to get active document: {e}")
            return None

    def has_active_document(self) -> bool:
        """Check if there is an active document.

        Returns:
            True if a document is open and active, False otherwise.
        """
        try:
            return self.app.documents.length > 0
        except Exception:
            return False

    def get_photoshop_version(self) -> str:
        """Get Photoshop version string.

        Returns:
            Version string, or 'Unknown' if cannot be determined.
        """
        try:
            return str(self.app.version)
        except Exception as e:
            logger.error(f"Failed to get PS version: {e}")
            return "Unknown"
