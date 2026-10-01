"""Render the app icons in ``web/icons/`` (PNG, needed for installing on Android).

The design is ``web/favicon.svg`` (indigo rounded square with a white "×÷"), redrawn here from
simple shapes so no image library is needed. The maskable icon fills the whole square and
shrinks the glyph so it stays inside Android's 80% safe circle.
Usage: ``uv run python scripts/make_icons.py``.
"""

import math
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

ICONS = Path(__file__).resolve().parent.parent / "web" / "icons"
VIEWBOX = 32.0
INDIGO = (0x4F, 0x46, 0xE5)
WHITE = (0xFF, 0xFF, 0xFF)
STROKE_RADIUS = 1.2  # stroke-width 2.4 with round caps
SEGMENTS = (((9.0, 9.0), (15.0, 15.0)), ((15.0, 9.0), (9.0, 15.0)), ((18.0, 21.0), (25.0, 21.0)))
DOTS = (((21.5, 17.5), 1.4), ((21.5, 24.5), 1.4))
GLYPH_CENTRE = (17.0, 16.85)  # middle of the glyph's bounding box


@dataclass(frozen=True)
class Icon:
    name: str
    size: int
    corner_radius: float  # 0 = full bleed
    glyph_scale: float


def _segment_distance(
    px: float, py: float, a: tuple[float, float], b: tuple[float, float]
) -> float:
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _glyph_distance(x: float, y: float) -> float:
    """Signed distance (in viewBox units) from the white glyph's edge; negative inside."""
    strokes = (_segment_distance(x, y, a, b) - STROKE_RADIUS for a, b in SEGMENTS)
    dots = (math.hypot(x - cx, y - cy) - r for (cx, cy), r in DOTS)
    return min(*strokes, *dots)


def _background_distance(x: float, y: float, radius: float) -> float:
    half = VIEWBOX / 2
    qx = abs(x - half) - (half - radius)
    qy = abs(y - half) - (half - radius)
    return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - radius


def _coverage(distance: float, pixel: float) -> float:
    return max(0.0, min(1.0, 0.5 - distance / pixel))


def render(icon: Icon) -> bytes:
    """The icon as raw RGBA rows, each prefixed with PNG filter byte 0."""
    pixel = VIEWBOX / icon.size
    centre = VIEWBOX / 2
    rows = bytearray()
    for row in range(icon.size):
        rows.append(0)
        y = (row + 0.5) * pixel
        for column in range(icon.size):
            x = (column + 0.5) * pixel
            alpha = _coverage(_background_distance(x, y, icon.corner_radius), pixel)
            gx = (x - centre) / icon.glyph_scale + GLYPH_CENTRE[0]
            gy = (y - centre) / icon.glyph_scale + GLYPH_CENTRE[1]
            white = _coverage(_glyph_distance(gx, gy), pixel / icon.glyph_scale)
            rgb = (round(i + (w - i) * white) for i, w in zip(INDIGO, WHITE, strict=True))
            rows.extend((*rgb, round(255 * alpha)))
    return bytes(rows)


def png(size: int, rows: bytes) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows, 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    ICONS.mkdir(exist_ok=True)
    for icon in (
        Icon("icon-192.png", 192, corner_radius=8, glyph_scale=1),
        Icon("icon-512.png", 512, corner_radius=8, glyph_scale=1),
        Icon("icon-maskable-512.png", 512, corner_radius=0, glyph_scale=0.75),
    ):
        (ICONS / icon.name).write_bytes(png(icon.size, render(icon)))
        print(f"Wrote {ICONS / icon.name}")


if __name__ == "__main__":
    main()
