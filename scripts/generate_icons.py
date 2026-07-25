"""Generate PNG and ICO icon files from resources/icon.svg.

Run once after checkout or after editing icon.svg. Uses QtSvg via PySide6 so
no extra dependencies (e.g. Pillow, inkscape) are required.

Usage: python -m scripts.generate_icons
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "mailcerto" / "resources"
SVG_PATH = RESOURCES / "icon.svg"

# Standard Windows ICO sizes (in px). Keep ordered from largest to smallest.
ICO_SIZES = [256, 128, 64, 48, 32, 24, 16]
PNG_EXPORT_SIZES = [256, 128, 64, 48, 32]


def main() -> int:
    if not SVG_PATH.exists():
        print(f"[!] Missing SVG: {SVG_PATH}")
        return 1

    from PySide6.QtCore import Qt, QByteArray, QSize
    from PySide6.QtGui import QImage, QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer

    raw = QByteArray(SVG_PATH.read_bytes())
    renderer = QSvgRenderer(raw)
    if not renderer.isValid():
        print("[!] SVG could not be parsed by QSvgRenderer")
        return 1

    def render(size: int) -> QImage:
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing, True)
        renderer.render(painter)
        painter.end()
        return image

    # Export individual PNGs
    for size in PNG_EXPORT_SIZES:
        img = render(size)
        out = RESOURCES / f"icon_{size}x{size}.png"
        if not img.save(str(out), "PNG"):
            print(f"[!] Failed to write {out}")
            return 1
        print(f"[+] Wrote {out.relative_to(ROOT)}")

    # Export highest-res PNG as the default fallback PNG
    default_png = RESOURCES / "icon.png"
    if not render(256).save(str(default_png), "PNG"):
        print(f"[!] Failed to write {default_png}")
        return 1
    print(f"[+] Wrote {default_png.relative_to(ROOT)}")

    # Build an ICO file that bundles all sizes. We use a pure-python minimal
    # ICO writer so Pillow is not required.
    ico_path = RESOURCES / "icon.ico"
    images_bytes: list[tuple[int, int, bytes]] = []
    for size in ICO_SIZES:
        img = render(size)
        # Write as uncompressed 32-bit ARGB BMP (BITMAPINFOHEADER) without
        # color table. Qt's PNG writer is not suitable here for the embedded
        # image inside ICO; we use BMP variant with AND-mask omitted (it is
        # optional for 32-bit ARGB ICO entries, many tools do it too).
        w = h = size
        # BITMAPINFOHEADER (40 bytes) for icon: biHeight is 2x real height
        # because AND mask area follows XOR mask; we set AND mask height = 0
        # by providing a dummy zero-length padding at the end.
        header_size = 40
        bpp = 32
        stride = ((w * (bpp // 8) + 3) // 4) * 4  # BMP rows padded to 4 bytes
        xor_size = stride * h
        and_mask_size = 0  # ARGB channels carry alpha, so AND is optional
        dib_bytes = b""
        dib_bytes += header_size.to_bytes(4, "little")
        dib_bytes += w.to_bytes(4, "little")
        dib_bytes += (h * 2).to_bytes(4, "little")
        dib_bytes += (1).to_bytes(2, "little")          # color planes
        dib_bytes += bpp.to_bytes(2, "little")
        dib_bytes += (0).to_bytes(4, "little")          # compression: BI_RGB
        dib_bytes += (xor_size + and_mask_size).to_bytes(4, "little")
        dib_bytes += (0).to_bytes(4, "little")          # XPelsPerMeter
        dib_bytes += (0).to_bytes(4, "little")          # YPelsPerMeter
        dib_bytes += (0).to_bytes(4, "little")          # colors used
        dib_bytes += (0).to_bytes(4, "little")          # important colors

        # ARGB -> BGRA and flip rows (BMP is bottom-up)
        pixels = bytearray()
        # Read each row in reverse order via QImage.scanLine(row)
        for y in range(h - 1, -1, -1):
            scan = bytes(img.scanLine(y))[:stride]
            # Qt's Format_ARGB32 stores each pixel as little-endian [B,G,R,A],
            # which is exactly the BGRA ordering BMP requires.
            if len(scan) < stride:
                scan = scan + b"\x00" * (stride - len(scan))
            pixels += scan
        dib_bytes += bytes(pixels)
        if and_mask_size:
            dib_bytes += b"\x00" * and_mask_size

        images_bytes.append((w, h, dib_bytes))

    # ICO file header (6 bytes) + directory (16 bytes per entry) + image data
    icon_dir = b""
    icon_dir += (0).to_bytes(2, "little")   # reserved
    icon_dir += (1).to_bytes(2, "little")   # type: 1 = icon
    icon_dir += len(images_bytes).to_bytes(2, "little")

    dir_size = 6 + 16 * len(images_bytes)
    offset = dir_size
    data = b""
    for (w, h, dib_bytes) in images_bytes:
        entry = b""
        entry += bytes([w if w < 256 else 0, h if h < 256 else 0])
        entry += bytes([0])                   # color count: 0 -> no palette
        entry += bytes([0])                   # reserved
        entry += (1).to_bytes(2, "little")    # color planes
        entry += bpp.to_bytes(2, "little")
        entry += len(dib_bytes).to_bytes(4, "little")
        entry += offset.to_bytes(4, "little")
        icon_dir += entry
        data += dib_bytes
        offset += len(dib_bytes)

    ico_path.write_bytes(icon_dir + data)
    print(f"[+] Wrote {ico_path.relative_to(ROOT)} ({len(images_bytes)} sizes: {ICO_SIZES})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
