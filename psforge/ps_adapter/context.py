"""Context tracking for Photoshop state - documents, layers, selections."""

from typing import Any

from loguru import logger

from psforge.ps_adapter.application import PhotoshopApp


def get_context_info() -> dict[str, Any]:
    """Get comprehensive context information about current Photoshop state.

    This function executes JavaScript in Photoshop to retrieve:
    - Whether a document is open
    - Document details (name, dimensions, resolution, color mode, layer count, selection status)
    - Active layer details (name, type, opacity, blend mode, visibility, bounds, etc.)

    Returns:
        Dictionary containing context information with structure:
        {
            "has_document": bool,
            "document": {
                "name": str,
                "width": int,
                "height": int,
                "resolution": float,
                "color_mode": str,
                "bit_depth": int,
                "layer_count": int,
                "has_selection": bool,
            } or None,
            "active_layer": {
                "name": str,
                "kind": str,
                "opacity": float,
                "blend_mode": str,
                "visible": bool,
                "locked": bool,
                "is_background": bool,
                "bounds": {"left": int, "top": int, "right": int, "bottom": int}
            } or None
        }
    """
    ps_app = PhotoshopApp()

    # JavaScript to extract context information
    context_script = """
    (function() {
        var context = {
            has_document: false,
            document: null,
            active_layer: null
        };

        // Check if any document is open
        if (app.documents.length === 0) {
            return JSON.stringify(context);
        }

        context.has_document = true;
        var doc = app.activeDocument;

        // Get document information
        var colorModeMap = {
            1: "BITMAP",
            2: "GRAYSCALE",
            3: "INDEXED",
            4: "RGB",
            5: "CMYK",
            7: "MULTICHANNEL",
            8: "DUOTONE",
            9: "LAB"
        };

        var bitDepthMap = {
            1: 1,
            8: 8,
            16: 16,
            32: 32
        };

        context.document = {
            name: doc.name,
            width: parseInt(doc.width),
            height: parseInt(doc.height),
            resolution: parseFloat(doc.resolution),
            color_mode: colorModeMap[doc.mode] || "UNKNOWN",
            bit_depth: bitDepthMap[doc.bitsPerChannel] || 8,
            layer_count: doc.layers.length,
            has_selection: false
        };

        // Check for active selection
        try {
            var selBounds = doc.selection.bounds;
            if (selBounds) {
                context.document.has_selection = true;
            }
        } catch(e) {
            context.document.has_selection = false;
        }

        // Get active layer information
        if (doc.activeLayer) {
            var layer = doc.activeLayer;

            var layerKindMap = {
                1: "NORMAL",
                2: "TEXT",
                3: "SOLIDFILL",
                4: "GRADIENTFILL",
                5: "PATTERNFILL",
                6: "LEVELS",
                7: "CURVES",
                8: "COLORBALANCE",
                9: "BRIGHTNESSCONTRAST",
                10: "HUESATURATION",
                11: "SELECTIVECOLOR",
                12: "CHANNELMIXER",
                13: "GRADIENTMAP",
                14: "INVERT",
                15: "THRESHOLD",
                16: "POSTERIZE",
                17: "SMARTOBJECT",
                18: "PHOTOFILTER",
                19: "EXPOSURE",
                20: "VIBRANCE",
                21: "VIDEO",
                22: "3D",
                23: "LAYER3D"
            };

            var blendModeMap = {
                "NORMAL": "NORMAL",
                "DISSOLVE": "DISSOLVE",
                "DARKEN": "DARKEN",
                "MULTIPLY": "MULTIPLY",
                "COLORBURN": "COLORBURN",
                "LINEARBURN": "LINEARBURN",
                "DARKERCOLOR": "DARKERCOLOR",
                "LIGHTEN": "LIGHTEN",
                "SCREEN": "SCREEN",
                "COLORDODGE": "COLORDODGE",
                "LINEARDODGE": "LINEARDODGE",
                "LIGHTERCOLOR": "LIGHTERCOLOR",
                "OVERLAY": "OVERLAY",
                "SOFTLIGHT": "SOFTLIGHT",
                "HARDLIGHT": "HARDLIGHT",
                "VIVIDLIGHT": "VIVIDLIGHT",
                "LINEARLIGHT": "LINEARLIGHT",
                "PINLIGHT": "PINLIGHT",
                "HARDMIX": "HARDMIX",
                "DIFFERENCE": "DIFFERENCE",
                "EXCLUSION": "EXCLUSION",
                "SUBTRACT": "SUBTRACT",
                "DIVIDE": "DIVIDE",
                "HUE": "HUE",
                "SATURATION": "SATURATION",
                "COLOR": "COLOR",
                "LUMINOSITY": "LUMINOSITY"
            };

            var isBackground = false;
            try {
                isBackground = layer.isBackgroundLayer;
            } catch(e) {
                isBackground = false;
            }

            var bounds = {left: 0, top: 0, right: 0, bottom: 0};
            try {
                bounds = {
                    left: parseInt(layer.bounds[0]),
                    top: parseInt(layer.bounds[1]),
                    right: parseInt(layer.bounds[2]),
                    bottom: parseInt(layer.bounds[3])
                };
            } catch(e) {}

            context.active_layer = {
                name: layer.name,
                kind: layerKindMap[layer.kind] || "UNKNOWN",
                opacity: parseFloat(layer.opacity),
                blend_mode: blendModeMap[layer.blendMode.toString()] || "NORMAL",
                visible: layer.visible,
                locked: layer.allLocked || layer.pixelsLocked,
                is_background: isBackground,
                bounds: bounds
            };
        }

        return JSON.stringify(context);
    })();
    """

    try:
        result = ps_app.execute_javascript(context_script)

        # Parse JSON result
        import json

        if isinstance(result, str):
            context = json.loads(result)
        else:
            context = result

        logger.debug(f"Context retrieved: {context}")
        return context

    except Exception as e:
        logger.error(f"Failed to get context info: {e}")

        # Return minimal error context
        return {
            "has_document": False,
            "document": None,
            "active_layer": None,
            "error": str(e),
        }
