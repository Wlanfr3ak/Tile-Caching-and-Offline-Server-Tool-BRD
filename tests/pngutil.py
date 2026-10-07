#!/usr/bin/env python3
"""PNG-Helfer für Tests — erzeugt gültige PNGs nur mit Stdlib."""
import struct
import zlib


def _chunk(typ: bytes, payload: bytes) -> bytes:
    return (struct.pack('>I', len(payload)) + typ + payload
            + struct.pack('>I', zlib.crc32(typ + payload) & 0xFFFFFFFF))


def make_png(w=256, h=256, pixel=(255, 255, 255, 255), vary=False):
    """Erzeugt ein gültiges RGBA-PNG (colortype 6, bitdepth 8).

    pixel: RGBA-Tupel für alle Pixel (z. B. (255,255,255,255) = opak weiß,
           (0,0,0,0) = transparent).
    vary:  True -> nicht-einheitliches Muster (steht für 'echte' Kacheln).
    """
    rows = bytearray()
    for y in range(h):
        rows.append(0)  # Filter: none
        for x in range(w):
            if vary:
                v = (x * 3 + y * 7) % 256
                rows += bytes((v, 255 - v, (x * y) % 256, 255))
            else:
                rows += bytes(pixel)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n'
            + _chunk(b'IHDR', ihdr)
            + _chunk(b'IDAT', zlib.compress(bytes(rows)))
            + _chunk(b'IEND', b''))


PNG_REAL = make_png(vary=True)                 # nicht-einheitlich -> 'echt'
PNG_EMPTY = make_png(pixel=(0, 0, 0, 0))       # volltransparent
PNG_WHITE = make_png(pixel=(255, 255, 255, 255))  # opak weiß (alte Cache-Leichen)
