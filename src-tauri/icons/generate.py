"""Generate app icons with stdlib only (no Pillow/network).

Navy rounded square, axes, white parabola, mint vertex dot. Emits PNGs plus a
multi-size ICO (PNG payloads — valid for Vista+). Run: python generate.py
"""

import math
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).parent
NAVY = (17, 26, 46)
WHITE = (245, 247, 255)
GRID = (79, 124, 255)
MINT = (34, 195, 139)


def _png(width: int, height: int, pixels: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


def _paint(size: int) -> bytes:
    buf = bytearray(size * size * 3)
    r = size * 0.22
    cx = cy = size / 2

    def setpx(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < size and 0 <= y < size:
            i = (y * size + x) * 3
            buf[i:i + 3] = bytes(color)

    for y in range(size):
        for x in range(size):
            dx = max(abs(x - cx) - (size / 2 - r), 0)
            dy = max(abs(y - cy) - (size / 2 - r), 0)
            if math.hypot(dx, dy) <= r:
                setpx(x, y, NAVY)
    # Axes.
    for x in range(size):
        setpx(x, size // 2, GRID)
    for y in range(size):
        setpx(size // 2, y, GRID)
    # Parabola opening upward around (vx, mid).
    k = 0.35 * 2.2 / size
    vx, mid = size * 0.5, size * 0.5
    for px in range(size):
        py = int(mid + k * (px - vx) ** 2)
        for oy in (-1, 0, 1):
            setpx(px, py + oy, WHITE)
    # Vertex dot.
    for oy in range(-2, 3):
        for ox in range(-2, 3):
            if ox * ox + oy * oy <= 5:
                setpx(int(vx) + ox, int(size * 0.5) + oy, MINT)
    return bytes(buf)


def _downscale(pixels: bytes, src: int, dst: int) -> bytes:
    out = bytearray(dst * dst * 3)
    for y in range(dst):
        for x in range(dst):
            r = g = b = 0
            n = 0
            x0, x1 = x * src // dst, (x + 1) * src // dst
            y0, y1 = y * src // dst, (y + 1) * src // dst
            for sy in range(y0, max(y0 + 1, y1)):
                for sx in range(x0, max(x0 + 1, x1)):
                    i = (sy * src + sx) * 3
                    r += pixels[i]
                    g += pixels[i + 1]
                    b += pixels[i + 2]
                    n += 1
            i = (y * dst + x) * 3
            out[i:i + 3] = bytes((r // n, g // n, b // n))
    return bytes(out)


def _ico(images: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory, payload = b"", b""
    for size, png in images:
        directory += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32,
                                 len(png), offset)
        offset += len(png)
        payload += png
    return header + directory + payload


def main() -> None:
    base = _paint(512)
    (HERE / "icon.png").write_bytes(_png(512, 512, base))
    sizes = {"32x32.png": 32, "128x128.png": 128, "128x128@2x.png": 256}
    for name, size in sizes.items():
        (HERE / name).write_bytes(_png(size, size, _downscale(base, 512, size)))
    ico_parts = []
    for size in (16, 32, 48, 256):
        small = _downscale(base, 512, size)
        ico_parts.append((size, _png(size, size, small)))
    (HERE / "icon.ico").write_bytes(_ico(ico_parts))
    print("icons written:", sorted(p.name for p in HERE.glob("*.png")) + ["icon.ico"])


if __name__ == "__main__":
    main()
