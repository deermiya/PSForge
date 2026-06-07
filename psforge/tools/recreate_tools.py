"""Layered PSD recreation tools.

The recreation workflow intentionally avoids screen automation. Python creates
small transparent asset layers with the standard library, then Photoshop places
them once and saves a PSD. Editable text stays as Photoshop text layers.
"""

from __future__ import annotations

import json
import math
import shutil
import struct
import tempfile
import zlib
from pathlib import Path
from typing import Any, Literal

from loguru import logger

from psforge.decorators import debug_tool, log_tool_call
from psforge.ps_adapter.application import PhotoshopApp
from psforge.registry import register_tool

RecreateMode = Literal["fast", "balanced", "source"]
Pixel = tuple[int, int, int, int]


def _escape_js_path(path: str | Path) -> str:
    return str(path).replace("\\", "\\\\")


def _default_output_paths(reference_image_path: str, suffix: str) -> tuple[str, str]:
    ref = Path(reference_image_path)
    return (
        str(ref.parent / f"{ref.stem}_{suffix}.psd"),
        str(ref.parent / f"{ref.stem}_{suffix}_preview.png"),
    )


def _read_image_size(path: str | Path) -> tuple[int, int]:
    """Read PNG/JPEG dimensions without external dependencies."""
    data = Path(path).read_bytes()

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])

    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            length = struct.unpack(">H", data[i : i + 2])[0]
            if marker in range(0xC0, 0xC4) or marker in range(0xC5, 0xC8) or marker in range(0xC9, 0xCC):
                height = struct.unpack(">H", data[i + 3 : i + 5])[0]
                width = struct.unpack(">H", data[i + 5 : i + 7])[0]
                return width, height
            i += length

    raise ValueError(f"Unsupported image format or unreadable dimensions: {path}")


def _blank(width: int, height: int) -> bytearray:
    return bytearray(width * height * 4)


def _blend_pixel(buf: bytearray, width: int, height: int, x: int, y: int, color: Pixel) -> None:
    if x < 0 or y < 0 or x >= width or y >= height:
        return

    r, g, b, a = color
    if a <= 0:
        return

    idx = (y * width + x) * 4
    dst_a = buf[idx + 3]
    src_a = a / 255.0
    inv = 1.0 - src_a
    out_a = a + dst_a * inv
    if out_a <= 0:
        return

    buf[idx] = int(r * src_a + buf[idx] * inv)
    buf[idx + 1] = int(g * src_a + buf[idx + 1] * inv)
    buf[idx + 2] = int(b * src_a + buf[idx + 2] * inv)
    buf[idx + 3] = min(255, int(out_a))


def _fill_rect(buf: bytearray, width: int, height: int, box: tuple[int, int, int, int], color: Pixel) -> None:
    x1, y1, x2, y2 = box
    for y in range(max(0, y1), min(height, y2)):
        for x in range(max(0, x1), min(width, x2)):
            _blend_pixel(buf, width, height, x, y, color)


def _fill_ellipse(buf: bytearray, width: int, height: int, cx: float, cy: float, rx: float, ry: float, color: Pixel) -> None:
    if rx <= 0 or ry <= 0:
        return
    x1 = int(max(0, cx - rx))
    x2 = int(min(width - 1, cx + rx))
    y1 = int(max(0, cy - ry))
    y2 = int(min(height - 1, cy + ry))
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1:
                _blend_pixel(buf, width, height, x, y, color)


def _fill_rounded_rect(
    buf: bytearray,
    width: int,
    height: int,
    box: tuple[int, int, int, int],
    radius: int,
    color: Pixel,
) -> None:
    x1, y1, x2, y2 = box
    _fill_rect(buf, width, height, (x1 + radius, y1, x2 - radius, y2), color)
    _fill_rect(buf, width, height, (x1, y1 + radius, x2, y2 - radius), color)
    _fill_ellipse(buf, width, height, x1 + radius, y1 + radius, radius, radius, color)
    _fill_ellipse(buf, width, height, x2 - radius, y1 + radius, radius, radius, color)
    _fill_ellipse(buf, width, height, x1 + radius, y2 - radius, radius, radius, color)
    _fill_ellipse(buf, width, height, x2 - radius, y2 - radius, radius, radius, color)


def _fill_polygon(buf: bytearray, width: int, height: int, points: list[tuple[float, float]], color: Pixel) -> None:
    if len(points) < 3:
        return
    min_x = int(max(0, min(p[0] for p in points)))
    max_x = int(min(width - 1, max(p[0] for p in points)))
    min_y = int(max(0, min(p[1] for p in points)))
    max_y = int(min(height - 1, max(p[1] for p in points)))

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            inside = False
            j = len(points) - 1
            for i in range(len(points)):
                xi, yi = points[i]
                xj, yj = points[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-6) + xi:
                    inside = not inside
                j = i
            if inside:
                _blend_pixel(buf, width, height, x, y, color)


def _draw_soft_line(
    buf: bytearray,
    width: int,
    height: int,
    p1: tuple[float, float],
    p2: tuple[float, float],
    line_width: float,
    color: Pixel,
) -> None:
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 0.01:
        return

    radius = max(0.8, line_width / 2.0)
    pad = int(radius + 2)
    min_x = int(max(0, min(x1, x2) - pad))
    max_x = int(min(width - 1, max(x1, x2) + pad))
    min_y = int(max(0, min(y1, y2) - pad))
    max_y = int(min(height - 1, max(y1, y2) + pad))

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            py = y + 0.5
            t = ((px - x1) * dx + (py - y1) * dy) / length_sq
            t = max(0.0, min(1.0, t))
            qx = x1 + t * dx
            qy = y1 + t * dy
            dist = math.hypot(px - qx, py - qy)
            if dist <= radius + 1.0:
                falloff = max(0.0, min(1.0, radius + 1.0 - dist))
                r, g, b, a = color
                _blend_pixel(buf, width, height, x, y, (r, g, b, int(a * falloff)))


def _write_png(path: Path, width: int, height: int, rgba: bytearray) -> None:
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * stride : (y + 1) * stride])

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def _save_layer(path: Path, width: int, height: int, rgba: bytearray) -> str:
    _write_png(path, width, height, rgba)
    return str(path)


def _make_assets(width: int, height: int, mode: RecreateMode, assets_dir: Path) -> list[dict[str, str | bool]]:
    assets: list[dict[str, str | bool]] = []

    def add(name: str, rgba: bytearray) -> None:
        path = assets_dir / f"{name}.png"
        assets.append({"name": name.replace("_", " ").title(), "path": _save_layer(path, width, height, rgba), "visible": True})

    glow = _blank(width, height)
    for y in range(height):
        for x in range(width):
            dx = (x - width * 0.5) / (width * 0.5)
            dy = (y - height * 0.55) / (height * 0.55)
            force = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy)) ** 2
            if force:
                _blend_pixel(glow, width, height, x, y, (255, 50, 75, int(42 * force)))
    add("background_center_glow", glow)

    shadow = _blank(width, height)
    _fill_ellipse(shadow, width, height, width * 0.5, height * 0.69, width * 0.28, height * 0.033, (35, 0, 12, 48))
    add("product_shadow", shadow)

    body = _blank(width, height)
    body_box = (int(width * 0.255), int(height * 0.500), int(width * 0.745), int(height * 0.667))
    _fill_rounded_rect(body, width, height, body_box, int(width * 0.095), (145, 5, 31, 235))
    _fill_rect(body, width, height, (int(width * 0.37), body_box[1] + 8, int(width * 0.62), body_box[3] - 10), (255, 62, 80, 34))
    _fill_rect(body, width, height, (int(width * 0.32), body_box[1] + 12, int(width * 0.34), body_box[3] - 12), (255, 230, 236, 62))
    _fill_rect(body, width, height, (int(width * 0.675), body_box[1] + 12, int(width * 0.695), body_box[3] - 12), (40, 0, 12, 82))
    add("product_body", body)

    lid = _blank(width, height)
    lid_box = (int(width * 0.28), int(height * 0.447), int(width * 0.72), int(height * 0.540))
    _fill_rounded_rect(lid, width, height, lid_box, int(width * 0.060), (178, 8, 31, 238))
    _fill_rect(lid, width, height, (lid_box[0] + 4, lid_box[3] - 12, lid_box[2] - 4, lid_box[3]), (58, 0, 13, 120))
    _fill_rect(lid, width, height, (lid_box[0] + 9, lid_box[1] + int(height * 0.05), lid_box[2] - 9, lid_box[1] + int(height * 0.054)), (255, 205, 216, 80))
    add("product_lid", lid)

    label = _blank(width, height)
    _fill_rect(label, width, height, (int(width * 0.307), int(height * 0.562), int(width * 0.693), int(height * 0.630)), (82, 0, 22, 125))
    add("product_label_panel", label)

    counts = {"fast": 5, "balanced": 10, "source": 16}
    for i in range(counts[mode]):
        stroke = _blank(width, height)
        cx = width * (0.50 + (((i * 37) % 17) - 8) / 1000)
        cy = height * (0.57 + (((i * 29) % 31) - 15) / 1000)
        rx = width * (0.22 + ((i * 11) % 12) / 100)
        ry = height * (0.23 + ((i * 7) % 15) / 100)
        rot = math.radians(-36 + ((i * 23) % 72))
        start = math.radians((i * 13) % 40)
        end = math.radians(330 + ((i * 17) % 50))
        steps = {"fast": 110, "balanced": 150, "source": 190}[mode]
        pts = []
        for s in range(steps + 1):
            a = start + (end - start) * s / steps
            x = math.cos(a) * rx
            y = math.sin(a) * ry
            pts.append((x * math.cos(rot) - y * math.sin(rot) + cx, x * math.sin(rot) + y * math.cos(rot) + cy))

        color = (255, 186, 214, 120) if i % 5 == 0 else (255, 250, 253, 165)
        line_width = 1.2 + ((i * 5) % 5) * 0.25
        for p1, p2 in zip(pts, pts[1:]):
            _draw_soft_line(stroke, width, height, p1, p2, line_width, color)
        add(f"energy_stroke_{i + 1:02d}", stroke)

    return assets


def _make_wpa_assets(width: int, height: int, mode: RecreateMode, assets_dir: Path) -> list[dict[str, str | bool]]:
    assets: list[dict[str, str | bool]] = []
    red = (184, 76, 86, 255)
    dark = (38, 42, 39, 255)
    ochre = (195, 176, 105, 255)

    def sx(x: float) -> float:
        return x * width

    def sy(y: float) -> float:
        return y * height

    def add(name: str, rgba: bytearray) -> None:
        path = assets_dir / f"{name}.png"
        assets.append({"name": name.replace("_", " ").title(), "path": _save_layer(path, width, height, rgba), "visible": True})

    ovals = _blank(width, height)
    _fill_ellipse(ovals, width, height, sx(0.50), sy(0.245), sx(0.47), sy(0.235), dark)
    _fill_ellipse(ovals, width, height, sx(0.50), sy(0.765), sx(0.47), sy(0.215), dark)
    add("poster_black_oval_fields", ovals)

    figure = _blank(width, height)
    _fill_ellipse(figure, width, height, sx(0.50), sy(0.215), sx(0.235), sy(0.175), red)
    _fill_rect(figure, width, height, (int(sx(0.34)), int(sy(0.31)), int(sx(0.64)), int(sy(0.445))), red)
    _fill_polygon(figure, width, height, [(sx(0.07), sy(0.20)), (sx(0.33), sy(0.44)), (sx(0.20), sy(0.44)), (sx(0.02), sy(0.25))], red)
    _fill_polygon(figure, width, height, [(sx(0.93), sy(0.20)), (sx(0.67), sy(0.44)), (sx(0.82), sy(0.44)), (sx(0.98), sy(0.25))], red)
    add("red_figure_and_hands_fill", figure)

    bands = _blank(width, height)
    _fill_rect(bands, width, height, (int(sx(0.02)), int(sy(0.435)), int(sx(0.98)), int(sy(0.515))), ochre)
    _fill_rect(bands, width, height, (int(sx(0.02)), int(sy(0.535)), int(sx(0.98)), int(sy(0.615))), ochre)
    _fill_rect(bands, width, height, (int(sx(0.02)), int(sy(0.515)), int(sx(0.98)), int(sy(0.525))), dark)
    _fill_rect(bands, width, height, (int(sx(0.02)), int(sy(0.615)), int(sx(0.98)), int(sy(0.625))), dark)
    add("blank_ochre_title_bands", bands)

    badge = _blank(width, height)
    _fill_polygon(badge, width, height, [(sx(0.35), sy(0.895)), (sx(0.65), sy(0.895)), (sx(0.70), sy(0.965)), (sx(0.30), sy(0.965))], ochre)
    add("bottom_ochre_badge_shape", badge)

    line = _blank(width, height)
    lw = 6 if mode == "fast" else 8
    # Head, face, hands.
    for p1, p2 in [
        ((0.34, 0.19), (0.43, 0.09)), ((0.43, 0.09), (0.58, 0.08)), ((0.58, 0.08), (0.68, 0.19)),
        ((0.34, 0.19), (0.35, 0.44)), ((0.66, 0.20), (0.64, 0.44)), ((0.37, 0.39), (0.50, 0.43)),
        ((0.50, 0.43), (0.61, 0.39)), ((0.03, 0.24), (0.23, 0.43)), ((0.23, 0.43), (0.34, 0.45)),
        ((0.97, 0.24), (0.77, 0.43)), ((0.77, 0.43), (0.64, 0.45)),
    ]:
        _draw_soft_line(line, width, height, (sx(p1[0]), sy(p1[1])), (sx(p2[0]), sy(p2[1])), lw, ochre)
    for x in [0.06, 0.09, 0.12, 0.15, 0.88, 0.91, 0.94, 0.97]:
        _draw_soft_line(line, width, height, (sx(x), sy(0.24)), (sx(x - 0.08 if x < 0.5 else x + 0.08), sy(0.39)), 4, ochre)
    # Eyes, nose, lips.
    for p1, p2 in [((0.28, 0.265), (0.42, 0.285)), ((0.57, 0.27), (0.69, 0.225)), ((0.48, 0.31), (0.50, 0.36)), ((0.43, 0.385), (0.56, 0.375))]:
        _draw_soft_line(line, width, height, (sx(p1[0]), sy(p1[1])), (sx(p2[0]), sy(p2[1])), 4, ochre)
    _fill_ellipse(line, width, height, sx(0.37), sy(0.285), sx(0.045), sy(0.017), ochre)
    _fill_ellipse(line, width, height, sx(0.62), sy(0.265), sx(0.042), sy(0.017), ochre)
    _fill_ellipse(line, width, height, sx(0.50), sy(0.39), sx(0.075), sy(0.017), ochre)
    add("ochre_face_and_hand_linework", line)

    hair = _blank(width, height)
    hair_lines = 8 if mode == "fast" else 15 if mode == "balanced" else 23
    for i in range(hair_lines):
        y = 0.09 + i * 0.012
        pts = []
        for s in range(80):
            t = s / 79
            x = 0.20 + 0.46 * t
            pts.append((sx(x), sy(y + math.sin(t * math.pi * 4 + i * 0.7) * 0.009 + t * 0.05)))
        for p1, p2 in zip(pts, pts[1:]):
            _draw_soft_line(hair, width, height, p1, p2, 5, ochre)
    add("wavy_ochre_hair_strokes", hair)

    decor = _blank(width, height)
    for side in [-1, 1]:
        base = 0.18 if side < 0 else 0.82
        for i in range(5):
            x1 = base + side * i * 0.025
            _draw_soft_line(decor, width, height, (sx(x1), sy(0.085)), (sx(x1 - side * 0.05), sy(0.28)), 3, red if i % 2 else ochre)
        leaf_x = 0.16 if side < 0 else 0.84
        _draw_soft_line(decor, width, height, (sx(leaf_x), sy(0.83)), (sx(leaf_x - side * 0.12), sy(0.95)), 5, red)
        for i in range(7):
            yy = 0.84 + i * 0.025
            _draw_soft_line(decor, width, height, (sx(leaf_x - side * 0.02), sy(yy)), (sx(leaf_x - side * 0.16), sy(yy + 0.035)), 4, red)
            _draw_soft_line(decor, width, height, (sx(leaf_x - side * 0.02), sy(yy)), (sx(leaf_x + side * 0.04), sy(yy + 0.055)), 3, red)
    add("red_floral_and_leaf_decoration", decor)

    texture = _blank(width, height)
    for i in range(380 if mode == "source" else 180):
        x = (i * 73) % width
        y = (i * 151) % height
        a = 18 + (i % 20)
        _fill_rect(texture, width, height, (x, y, min(width, x + 2), min(height, y + 2)), (245, 230, 180, a))
    add("subtle_vintage_print_texture", texture)
    return assets


def _make_color_separated_assets(reference_image_path: str | Path, assets_dir: Path) -> list[dict[str, str | bool]]:
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("poster_color_separation preset requires Pillow. Install it with: pip install pillow") from e

    img = Image.open(reference_image_path).convert("RGB")
    width, height = img.size
    layers = {
        "black_ink_from_source": Image.new("RGBA", (width, height), (0, 0, 0, 0)),
        "ochre_blocks_from_source": Image.new("RGBA", (width, height), (0, 0, 0, 0)),
        "red_artwork_from_source": Image.new("RGBA", (width, height), (0, 0, 0, 0)),
        "paper_edge_and_print_wear": Image.new("RGBA", (width, height), (0, 0, 0, 0)),
    }

    src = img.load()
    black = layers["black_ink_from_source"].load()
    ochre = layers["ochre_blocks_from_source"].load()
    red = layers["red_artwork_from_source"].load()
    wear = layers["paper_edge_and_print_wear"].load()

    for y in range(height):
        for x in range(width):
            r, g, b = src[x, y]
            lum = (r * 299 + g * 587 + b * 114) // 1000
            if lum < 78 and not (r > 95 and r > g + 14 and r > b + 20):
                black[x, y] = (r, g, b, 255)
            elif r > 145 and g > 120 and b < 125 and abs(r - g) < 55:
                ochre[x, y] = (r, g, b, 255)
            elif r > 92 and r > g + 10 and r > b + 8:
                red[x, y] = (r, g, b, 255)
            elif lum > 128 or (abs(r - g) < 20 and abs(g - b) < 20):
                wear[x, y] = (r, g, b, 185)

    assets: list[dict[str, str | bool]] = []
    for name, layer in layers.items():
        path = assets_dir / f"{name}.png"
        layer.save(path, "PNG")
        assets.append({"name": name.replace("_", " ").title(), "path": str(path), "visible": True})
    return assets


def _build_recreation_script(
    reference_image_path: str,
    output_psd_path: str,
    output_preview_path: str,
    mode: RecreateMode,
    preset: str,
    assets: list[dict[str, str | bool]],
) -> str:
    if preset == "wpa_vintage_poster":
        return _build_wpa_recreation_script(reference_image_path, output_psd_path, output_preview_path, mode, preset, assets)
    if preset == "poster_color_separation":
        return _build_color_separation_script(reference_image_path, output_psd_path, output_preview_path, mode, preset, assets)

    assets_json = json.dumps(assets, ensure_ascii=False, separators=(",", ":"))

    return f"""
(function() {{
    try {{
        app.displayDialogs = DialogModes.NO;
        var refFile = new File("{_escape_js_path(reference_image_path)}");
        if (!refFile.exists) return JSON.stringify({{success:false,error:"Reference image does not exist"}});

        var refDoc = app.open(refFile);
        var width = parseInt(refDoc.width);
        var height = parseInt(refDoc.height);
        refDoc.selection.selectAll();
        refDoc.selection.copy();
        refDoc.close(SaveOptions.DONOTSAVECHANGES);

        var doc = app.documents.add(width, height, 72, "PSForge_Layered_Recreation", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        var layerNames = [];

        function rgb(r,g,b) {{
            var c = new SolidColor();
            c.rgb.red = r; c.rgb.green = g; c.rgb.blue = b;
            return c;
        }}

        function remember(layer) {{
            layerNames.push(layer.name);
            return layer;
        }}

        function fillLayer(name, r, g, b) {{
            var layer = doc.artLayers.add();
            layer.name = name;
            doc.activeLayer = layer;
            doc.selection.select([[0,0],[width,0],[width,height],[0,height]]);
            doc.selection.fill(rgb(r,g,b), ColorBlendMode.NORMAL, 100, false);
            doc.selection.deselect();
            return remember(layer);
        }}

        function pasteFile(path, name, visible) {{
            var f = new File(path);
            var src = app.open(f);
            src.selection.selectAll();
            src.selection.copy();
            src.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;
            var layer = doc.paste();
            layer.name = name;
            layer.visible = visible;
            return remember(layer);
        }}

        function addText(name, text, size, font, x, y, r, g, b, opacity) {{
            var layer = doc.artLayers.add();
            layer.kind = LayerKind.TEXT;
            layer.name = name;
            layer.opacity = opacity || 100;
            var item = layer.textItem;
            item.contents = text;
            item.size = size;
            item.font = font;
            item.color = rgb(r,g,b);
            item.position = [x,y];
            try {{ item.justification = Justification.CENTER; }} catch(e) {{}}
            return remember(layer);
        }}

        var refLayer = doc.paste();
        refLayer.name = "[Reference] Original image";
        refLayer.visible = false;
        remember(refLayer);

        fillLayer("Background base red", 184, 0, 30);

        var assets = {assets_json};
        for (var i = 0; i < assets.length; i++) {{
            pasteFile(assets[i].path, assets[i].name, assets[i].visible);
        }}

        addText("Product label SK-II - editable", "SK-II", Math.max(14, width * 0.068), "TimesNewRomanPSMT", width * 0.50, height * 0.592, 255, 255, 255, 100);
        addText("Product label R.N.A.Power - editable", "R.N.A.POWER", Math.max(5, width * 0.025), "ArialMT", width * 0.50, height * 0.615, 255, 232, 236, 100);
        addText("Product label lotion - editable", "AIRY MILKY LOTION", Math.max(5, width * 0.020), "ArialMT", width * 0.50, height * 0.632, 255, 224, 230, 100);
        addText("Power handwriting - editable", "Power", Math.max(38, width * 0.16), "SegoeScript", width * 0.50, height * 0.437, 255, 255, 255, 94);
        addText("Logo text - editable", "SK-II", Math.max(42, width * 0.17), "TimesNewRomanPSMT", width * 0.50, height * 0.117, 255, 255, 255, 100);

        var psdFile = new File("{_escape_js_path(output_psd_path)}");
        var psdOptions = new PhotoshopSaveOptions();
        psdOptions.layers = true;
        doc.saveAs(psdFile, psdOptions, true, Extension.LOWERCASE);

        var previewDoc = doc.duplicate("PSForge_Layered_Recreation_preview", true);
        previewDoc.flatten();
        var pngFile = new File("{_escape_js_path(output_preview_path)}");
        var pngOptions = new PNGSaveOptions();
        pngOptions.compression = 6;
        pngOptions.interlaced = false;
        previewDoc.saveAs(pngFile, pngOptions, true, Extension.LOWERCASE);
        previewDoc.close(SaveOptions.DONOTSAVECHANGES);

        return JSON.stringify({{
            success: true,
            preset: "{preset}",
            mode: "{mode}",
            width: width,
            height: height,
            layer_count: layerNames.length,
            psd_path: "{_escape_js_path(output_psd_path)}",
            preview_path: "{_escape_js_path(output_preview_path)}",
            layers: layerNames
        }});
    }} catch(e) {{
        return JSON.stringify({{success:false,error:e.toString(),line:e.line}});
    }}
}})();
"""


def _build_color_separation_script(
    reference_image_path: str,
    output_psd_path: str,
    output_preview_path: str,
    mode: RecreateMode,
    preset: str,
    assets: list[dict[str, str | bool]],
) -> str:
    assets_json = json.dumps(assets, ensure_ascii=False, separators=(",", ":"))

    return f"""
(function() {{
    try {{
        app.displayDialogs = DialogModes.NO;
        var refFile = new File("{_escape_js_path(reference_image_path)}");
        if (!refFile.exists) return JSON.stringify({{success:false,error:"Reference image does not exist"}});

        var refDoc = app.open(refFile);
        var width = parseInt(refDoc.width);
        var height = parseInt(refDoc.height);
        refDoc.selection.selectAll();
        refDoc.selection.copy();
        refDoc.close(SaveOptions.DONOTSAVECHANGES);

        var doc = app.documents.add(width, height, 72, "PSForge_Color_Separated_Recreation", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        var layerNames = [];

        function rgb(r,g,b) {{
            var c = new SolidColor();
            c.rgb.red = r; c.rgb.green = g; c.rgb.blue = b;
            return c;
        }}

        function remember(layer) {{
            layerNames.push(layer.name);
            return layer;
        }}

        function fillLayer(name, r, g, b) {{
            var layer = doc.artLayers.add();
            layer.name = name;
            doc.activeLayer = layer;
            doc.selection.select([[0,0],[width,0],[width,height],[0,height]]);
            doc.selection.fill(rgb(r,g,b), ColorBlendMode.NORMAL, 100, false);
            doc.selection.deselect();
            return remember(layer);
        }}

        function pasteFile(path, name, visible) {{
            var f = new File(path);
            var src = app.open(f);
            src.selection.selectAll();
            src.selection.copy();
            src.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;
            var layer = doc.paste();
            layer.name = name;
            layer.visible = visible;
            return remember(layer);
        }}

        var refLayer = doc.paste();
        refLayer.name = "[Reference] Original poster hidden";
        refLayer.visible = false;
        remember(refLayer);

        fillLayer("Base muted red paper color", 184, 76, 86);

        var assets = {assets_json};
        for (var i = 0; i < assets.length; i++) {{
            pasteFile(assets[i].path, assets[i].name, assets[i].visible);
        }}

        var psdFile = new File("{_escape_js_path(output_psd_path)}");
        var psdOptions = new PhotoshopSaveOptions();
        psdOptions.layers = true;
        doc.saveAs(psdFile, psdOptions, true, Extension.LOWERCASE);

        var previewDoc = doc.duplicate("PSForge_Color_Separated_Recreation_preview", true);
        previewDoc.flatten();
        var pngFile = new File("{_escape_js_path(output_preview_path)}");
        var pngOptions = new PNGSaveOptions();
        pngOptions.compression = 6;
        pngOptions.interlaced = false;
        previewDoc.saveAs(pngFile, pngOptions, true, Extension.LOWERCASE);
        previewDoc.close(SaveOptions.DONOTSAVECHANGES);

        return JSON.stringify({{
            success: true,
            preset: "{preset}",
            mode: "{mode}",
            width: width,
            height: height,
            layer_count: layerNames.length,
            psd_path: "{_escape_js_path(output_psd_path)}",
            preview_path: "{_escape_js_path(output_preview_path)}",
            layers: layerNames
        }});
    }} catch(e) {{
        return JSON.stringify({{success:false,error:e.toString(),line:e.line}});
    }}
}})();
"""


def _build_wpa_recreation_script(
    reference_image_path: str,
    output_psd_path: str,
    output_preview_path: str,
    mode: RecreateMode,
    preset: str,
    assets: list[dict[str, str | bool]],
) -> str:
    assets_json = json.dumps(assets, ensure_ascii=False, separators=(",", ":"))

    return f"""
(function() {{
    try {{
        app.displayDialogs = DialogModes.NO;
        var refFile = new File("{_escape_js_path(reference_image_path)}");
        if (!refFile.exists) return JSON.stringify({{success:false,error:"Reference image does not exist"}});

        var refDoc = app.open(refFile);
        var width = parseInt(refDoc.width);
        var height = parseInt(refDoc.height);
        refDoc.selection.selectAll();
        refDoc.selection.copy();
        refDoc.close(SaveOptions.DONOTSAVECHANGES);

        var doc = app.documents.add(width, height, 72, "PSForge_WPA_Poster_Recreation", NewDocumentMode.RGB, DocumentFill.TRANSPARENT);
        var layerNames = [];

        function rgb(r,g,b) {{
            var c = new SolidColor();
            c.rgb.red = r; c.rgb.green = g; c.rgb.blue = b;
            return c;
        }}

        function remember(layer) {{
            layerNames.push(layer.name);
            return layer;
        }}

        function fillLayer(name, r, g, b) {{
            var layer = doc.artLayers.add();
            layer.name = name;
            doc.activeLayer = layer;
            doc.selection.select([[0,0],[width,0],[width,height],[0,height]]);
            doc.selection.fill(rgb(r,g,b), ColorBlendMode.NORMAL, 100, false);
            doc.selection.deselect();
            return remember(layer);
        }}

        function pasteFile(path, name, visible) {{
            var f = new File(path);
            var src = app.open(f);
            src.selection.selectAll();
            src.selection.copy();
            src.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;
            var layer = doc.paste();
            layer.name = name;
            layer.visible = visible;
            return remember(layer);
        }}

        function addText(name, text, size, font, x, y, r, g, b, opacity) {{
            var layer = doc.artLayers.add();
            layer.kind = LayerKind.TEXT;
            layer.name = name;
            layer.opacity = opacity || 100;
            var item = layer.textItem;
            item.contents = text;
            item.size = size;
            item.font = font;
            item.color = rgb(r,g,b);
            item.position = [x,y];
            try {{ item.justification = Justification.CENTER; }} catch(e) {{}}
            return remember(layer);
        }}

        var refLayer = doc.paste();
        refLayer.name = "[Reference] Original WPA poster";
        refLayer.visible = false;
        remember(refLayer);

        fillLayer("Background flat muted red", 184, 76, 86);

        var assets = {assets_json};
        for (var i = 0; i < assets.length; i++) {{
            pasteFile(assets[i].path, assets[i].name, assets[i].visible);
        }}

        addText("WPA script lettering - editable", "WPA", Math.max(90, width * 0.16), "SegoeScript", width * 0.50, height * 0.785, 184, 76, 86, 100);

        var psdFile = new File("{_escape_js_path(output_psd_path)}");
        var psdOptions = new PhotoshopSaveOptions();
        psdOptions.layers = true;
        doc.saveAs(psdFile, psdOptions, true, Extension.LOWERCASE);

        var previewDoc = doc.duplicate("PSForge_WPA_Poster_Recreation_preview", true);
        previewDoc.flatten();
        var pngFile = new File("{_escape_js_path(output_preview_path)}");
        var pngOptions = new PNGSaveOptions();
        pngOptions.compression = 6;
        pngOptions.interlaced = false;
        previewDoc.saveAs(pngFile, pngOptions, true, Extension.LOWERCASE);
        previewDoc.close(SaveOptions.DONOTSAVECHANGES);

        return JSON.stringify({{
            success: true,
            preset: "{preset}",
            mode: "{mode}",
            width: width,
            height: height,
            layer_count: layerNames.length,
            psd_path: "{_escape_js_path(output_psd_path)}",
            preview_path: "{_escape_js_path(output_preview_path)}",
            layers: layerNames
        }});
    }} catch(e) {{
        return JSON.stringify({{success:false,error:e.toString(),line:e.line}});
    }}
}})();
"""


def register(mcp) -> list[str]:
    """Register layered PSD recreation tools with MCP server."""
    registered_tools = []

    @debug_tool
    @log_tool_call
    def recreate_image_as_layered_psd(
        reference_image_path: str,
        output_psd_path: str | None = None,
        output_preview_path: str | None = None,
        mode: RecreateMode = "balanced",
        preset: str = "skincare_red_scribble",
    ) -> dict[str, Any]:
        """Recreate a reference image as a layered Photoshop PSD.

        The tool creates a hidden reference layer, separated bitmap
        construction layers, editable Photoshop text layers, and a PNG preview.
        It is optimized for low-token agent workflows: one MCP call, one
        Photoshop script, no screen recognition, and no mouse simulation.

        Args:
            reference_image_path: Absolute path to the reference image.
            output_psd_path: Optional PSD output path. Defaults beside the input image.
            output_preview_path: Optional PNG preview output path.
            mode: Detail level: "fast", "balanced", or "source".
            preset: Recreation preset. Currently optimized for "skincare_red_scribble".

        Returns:
            dict: success, PSD path, preview path, canvas size, layer count, layers.
        """
        if mode not in ("fast", "balanced", "source"):
            return {"success": False, "error": "mode must be one of: fast, balanced, source"}

        ref = Path(reference_image_path)
        if not ref.exists():
            return {"success": False, "error": f"Reference image does not exist: {reference_image_path}"}

        if output_psd_path is None or output_preview_path is None:
            default_psd, default_preview = _default_output_paths(reference_image_path, "layered_recreation")
            output_psd_path = output_psd_path or default_psd
            output_preview_path = output_preview_path or default_preview

        try:
            width, height = _read_image_size(ref)
            Path(output_psd_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_preview_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return {"success": False, "error": str(e)}

        assets_dir = Path(tempfile.mkdtemp(prefix="psforge_recreate_"))
        try:
            if preset == "poster_color_separation":
                assets = _make_color_separated_assets(ref, assets_dir)
            elif preset == "wpa_vintage_poster":
                assets = _make_wpa_assets(width, height, mode, assets_dir)
            else:
                assets = _make_assets(width, height, mode, assets_dir)
            script = _build_recreation_script(
                reference_image_path=reference_image_path,
                output_psd_path=output_psd_path,
                output_preview_path=output_preview_path,
                mode=mode,
                preset=preset,
                assets=assets,
            )

            ps_app = PhotoshopApp()
            logger.info(f"Recreating image as layered PSD: {reference_image_path}")
            raw = ps_app.execute_javascript(script)
            result = json.loads(raw) if isinstance(raw, str) else raw
            if not result.get("success"):
                return result

            return {
                "success": True,
                "message": f"Layered PSD recreated with {result['layer_count']} layers",
                **result,
            }
        except Exception as e:
            psd_exists = Path(output_psd_path).exists()
            preview_exists = Path(output_preview_path).exists()
            if psd_exists and preview_exists:
                logger.warning(f"Photoshop returned an error after saving outputs: {e}")
                return {
                    "success": True,
                    "message": "Layered PSD and preview were saved, but Photoshop returned an error while finishing the script",
                    "warning": str(e),
                    "preset": preset,
                    "mode": mode,
                    "width": width,
                    "height": height,
                    "layer_count": len(assets) + 7,
                    "psd_path": output_psd_path,
                    "preview_path": output_preview_path,
                }
            logger.error(f"Layered PSD recreation failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            shutil.rmtree(assets_dir, ignore_errors=True)

    registered_tools.append(register_tool(mcp, recreate_image_as_layered_psd, "recreate_image_as_layered_psd"))
    return registered_tools
