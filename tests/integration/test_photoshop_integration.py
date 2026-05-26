"""Integration tests for Photoshop connection and operations.

These tests require Photoshop to be running and will perform actual operations.
Run with: pytest tests/integration/test_photoshop_integration.py

⚠️  WARNING: These tests will create/modify documents in Photoshop.
   Make sure to save any important work before running.
"""

import pytest


@pytest.fixture(scope="module")
def ps_app():
    """Fixture to provide Photoshop application instance."""
    from psforge.ps_adapter.application import PhotoshopApp

    app = PhotoshopApp()
    yield app


@pytest.fixture(scope="function")
def clean_document(ps_app):
    """Fixture to ensure a clean document state before each test."""
    # Close all documents before test
    try:
        script = """
        while (app.documents.length > 0) {
            app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);
        }
        """
        ps_app.execute_javascript(script)
    except Exception:
        pass

    yield

    # Cleanup after test
    try:
        script = """
        while (app.documents.length > 0) {
            app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);
        }
        """
        ps_app.execute_javascript(script)
    except Exception:
        pass


class TestPhotoshopConnection:
    """Test basic Photoshop connection."""

    def test_connection_established(self, ps_app):
        """Test that connection to Photoshop is established."""
        assert ps_app is not None
        assert ps_app.app is not None

    def test_get_version(self, ps_app):
        """Test getting Photoshop version."""
        version = ps_app.get_photoshop_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_execute_javascript(self, ps_app):
        """Test JavaScript execution."""
        result = ps_app.execute_javascript("1 + 1;")
        # Result should be 2 or "2"
        assert str(result) == "2"


class TestContextInfo:
    """Test context information retrieval."""

    def test_get_context_info_no_document(self, ps_app, clean_document):
        """Test getting context info when no document is open."""
        from psforge.ps_adapter.context import get_context_info

        context = get_context_info()

        assert isinstance(context, dict)
        assert "has_document" in context
        assert context["has_document"] is False

    def test_get_context_info_with_document(self, ps_app, clean_document):
        """Test getting context info with an open document."""
        from psforge.ps_adapter.context import get_context_info

        # Create a test document
        ps_app.execute_javascript(
            """
            app.documents.add(800, 600, 72, "Test Document", NewDocumentMode.RGB);
        """
        )

        context = get_context_info()

        assert context["has_document"] is True
        assert "document" in context
        assert context["document"] is not None
        assert context["document"]["name"] == "Test Document"
        assert context["document"]["width"] == 800
        assert context["document"]["height"] == 600


class TestDocumentOperations:
    """Test document creation and manipulation."""

    def test_create_document(self, ps_app, clean_document):
        """Test creating a new document."""
        from psforge.tools.document_tools import register

        class MockMCP:
            def tool(self, name, description):
                return lambda func: func

        mcp = MockMCP()
        register(mcp)

        from psforge.tools import document_tools

        result = document_tools.create_document(width=1920, height=1080, name="Integration Test")

        assert result["success"] is True
        assert "context" in result
        assert result["context"]["has_document"] is True


class TestLayerOperations:
    """Test layer operations."""

    @pytest.fixture
    def document_with_layer(self, ps_app, clean_document):
        """Create a test document with a layer."""
        ps_app.execute_javascript(
            """
            var doc = app.documents.add(800, 600, 72, "Test", NewDocumentMode.RGB);
            var layer = doc.artLayers.add();
            layer.name = "Test Layer";
        """
        )
        yield
        # Cleanup happens in clean_document fixture

    def test_create_layer(self, ps_app, clean_document):
        """Test creating a new layer."""
        # Create document first
        ps_app.execute_javascript('app.documents.add(800, 600, 72, "Test", NewDocumentMode.RGB);')

        from psforge.tools.layer_tools import register

        class MockMCP:
            def tool(self, name, description):
                return lambda func: func

        mcp = MockMCP()
        register(mcp)

        from psforge.tools import layer_tools

        result = layer_tools.create_layer(name="Integration Layer")

        assert result["success"] is True
        assert result["layer_name"] == "Integration Layer"


# Note: Add more integration tests as needed
# Each test should be independent and clean up after itself


if __name__ == "__main__":
    print("⚠️  Integration tests require Photoshop to be running!")
    print("Run with: pytest tests/integration/test_photoshop_integration.py")
    print()
    print("Make sure to save any important work in Photoshop before running.")
