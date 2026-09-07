"""Minimal PNG/WebP header readers — no third-party dependency, no macOS `sips`,
so the build gate works anywhere. Returns (width, height) or None."""


def _png(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n" or b[12:16] != b"IHDR":
        return None
    return (int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big"))


def _webp(b):
    # Parse RIFF chunks properly. Scanning for b"VP8" with find() can match
    # inside compressed payload and silently return a wrong size.
    if len(b) < 16 or b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return None
    pos = 12
    while pos + 8 <= len(b):
        fourcc = b[pos:pos + 4]
        size = int.from_bytes(b[pos + 4:pos + 8], "little")
        body = b[pos + 8:pos + 8 + size]
        if fourcc == b"VP8X" and len(body) >= 10:
            return (int.from_bytes(body[4:7], "little") + 1,
                    int.from_bytes(body[7:10], "little") + 1)
        if fourcc == b"VP8L" and len(body) >= 5 and body[0] == 0x2F:
            n = int.from_bytes(body[1:5], "little")
            return ((n & 0x3FFF) + 1, ((n >> 14) & 0x3FFF) + 1)
        if fourcc == b"VP8 " and len(body) >= 10:
            if body[3:6] != b"\x9d\x01\x2a":
                return None
            return (int.from_bytes(body[6:8], "little") & 0x3FFF,
                    int.from_bytes(body[8:10], "little") & 0x3FFF)
        pos += 8 + size + (size & 1)      # chunks are padded to even length
    return None


def image_size(path):
    with open(path, "rb") as fh:
        b = fh.read(64 * 1024)
    if not b:
        return None
    return _png(b) if b[:8] == b"\x89PNG\r\n\x1a\n" else _webp(b)
