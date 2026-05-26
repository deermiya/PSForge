"""Action Manager interface for reading Photoshop state via descriptor API."""

from typing import Any

from loguru import logger


class ActionManager:
    """Manages interactions with Photoshop's Action Manager (Descriptor API)."""

    def __init__(self, app):
        """Initialize Action Manager with Photoshop application instance.

        Args:
            app: Photoshop application instance from photoshop-python-api.
        """
        self.app = app

    def execute_action_get(self, reference: str) -> dict[str, Any]:
        """Execute ActionDescriptor Get operation to retrieve PS state.

        Args:
            reference: The descriptor reference to query.

        Returns:
            Dictionary containing the retrieved state.
        """
        # This is a placeholder implementation
        # In practice, this would use photoshop-python-api's ActionDescriptor API
        # or execute JavaScript to query the Action Manager
        logger.debug(f"ActionManager.execute_action_get: {reference}")

        try:
            # For now, we'll use JavaScript execution as fallback
            script = f"""
            (function() {{
                try {{
                    var ref = new ActionReference();
                    ref.putProperty(charIDToTypeID('Prpr'), stringIDToTypeID('{reference}'));
                    ref.putEnumerated(charIDToTypeID('Dcmn'), charIDToTypeID('Ordn'), charIDToTypeID('Trgt'));
                    var desc = executeActionGet(ref);
                    return desc.toString();
                }} catch(e) {{
                    return 'Error: ' + e.toString();
                }}
            }})();
            """

            result = self.app.execute_javascript(script)
            return {"raw_result": result}

        except Exception as e:
            logger.error(f"ActionManager query failed: {e}")
            return {"error": str(e)}

    def get_document_property(self, property_name: str) -> Any:
        """Get a specific property of the active document.

        Args:
            property_name: Name of the property to retrieve.

        Returns:
            The property value, or None if not available.
        """
        try:
            script = f"""
            (function() {{
                if (!app.documents.length) return null;
                var doc = app.activeDocument;
                return doc.{property_name};
            }})();
            """

            return self.app.execute_javascript(script)

        except Exception as e:
            logger.error(f"Failed to get document property {property_name}: {e}")
            return None

    def get_layer_property(self, property_name: str) -> Any:
        """Get a specific property of the active layer.

        Args:
            property_name: Name of the property to retrieve.

        Returns:
            The property value, or None if not available.
        """
        try:
            script = f"""
            (function() {{
                if (!app.documents.length) return null;
                var layer = app.activeDocument.activeLayer;
                return layer.{property_name};
            }})();
            """

            return self.app.execute_javascript(script)

        except Exception as e:
            logger.error(f"Failed to get layer property {property_name}: {e}")
            return None
