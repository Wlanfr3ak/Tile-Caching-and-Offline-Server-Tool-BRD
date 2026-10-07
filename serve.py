#!/usr/bin/env python3
"""
Lokaler Tile-Server für offene WMS-/XYZ-Kartendienste (DOP, DTK, OSM).

Starten:
    python serve.py

Danach im Browser öffnen:
    http://localhost:8080

Fehlende Kacheln werden vom WMS geladen und unter ./tiles/{layer}/{z}/{x}/{y}.png
persistent gespeichert, sodass sie später auch offline oder von anderen Programmen
als XYZ-Tiles verwendet werden können.

Konfiguration:
    Die Datei config.json (lokal, nicht im Repo) enthält Port, Layer-Definitionen
    und Regionen. Fehlt sie, wird config.example.json bzw. die eingebauten
    Defaults verwendet. Siehe config.example.json für das Schema.
"""
import http.server
import json
import logging
import math
import os
import random
import re
import socketserver
import sys
import traceback
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_version():
    try:
        with open(os.path.join(ROOT, 'VERSION'), encoding='utf-8') as f:
            return f.read().strip() or '0.0.0'
    except OSError:
        return '0.0.0'


VERSION = _load_version()

logging.basicConfig(
    filename=os.path.join(ROOT, 'server.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'port': 8080,
    'min_zoom': 8,
    'user_agent': 'LocalTileViewer/1.0',
    'default_bbox': [51.2, 6.5, 55.3, 14.6],
    'layers': {
        'dtk5': {
            'type': 'wms',
            'base': 'https://service.gdi-sh.de/WMS_SH_DTK5_OpenGBD?',
            'layer': 'sh_dtk5_col',
            'max_zoom': 17,
            'bbox': [53.3, 7.8, 55.2, 11.5],
        },
        'dop20': {
            'type': 'wms',
            'base': 'https://dienste.gdi-sh.de/WMS_SH_DOP20col_OpenGBD?',
            'layer': 'sh_dop20_rgb',
            'max_zoom': 19,
            'bbox': [53.3, 7.8, 55.2, 11.5],
        },
        'ni_dop20': {
            'type': 'wms',
            'base': 'https://opendata.lgln.niedersachsen.de/doorman/noauth/dop_wms?',
            'layer': 'ni_dop20',
            'max_zoom': 19,
            'bbox': [51.3, 6.6, 54.0, 11.6],
        },
        'hh_dop': {
            'type': 'wms',
            'base': 'https://geodienste.hamburg.de/wms_dop_zeitreihe_belaubt?',
            'layer': 'dop_zeitreihe_belaubt',
            'max_zoom': 19,
            'bbox': [53.39, 9.72, 53.76, 10.35],
        },
        'hh_dop_u': {
            'type': 'wms',
            'base': 'https://geodienste.hamburg.de/wms_dop_zeitreihe_unbelaubt?',
            'layer': 'dop_zeitreihe_unbelaubt',
            'max_zoom': 19,
            'bbox': [53.39, 9.72, 53.76, 10.35],
        },
        'mv_dop': {
            'type': 'wms',
            'base': 'https://www.geodaten-mv.de/dienste/adv_dop?',
            'layer': 'mv_dop',
            'max_zoom': 19,
            'bbox': [53.05, 10.6, 54.69, 14.42],
        },
        'mv_dtk10': {
            'type': 'wms',
            'base': 'https://www.geodaten-mv.de/dienste/adv_dtk10?',
            'layer': 'mv_dtk10',
            'min_zoom': 15,
            'max_zoom': 18,
            'bbox': [53.05, 10.6, 54.69, 14.42],
        },
        'osm': {
            'type': 'xyz',
            'url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            'max_zoom': 19,
            'bbox': [51.2, 6.5, 55.3, 14.6],
        },
    },
}


def load_config():
    """Lädt config.json; Fallback: config.example.json; Fallback: Defaults."""
    for name in ('config.json', 'config.example.json'):
        path = os.path.join(ROOT, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                cfg = json.load(f)
            cfg = {**DEFAULT_CONFIG, **cfg}
            layers = {**DEFAULT_CONFIG['layers'], **cfg.get('layers', {})}
            # Meta-Schlüssel (z. B. "_schema") und ungültige Einträge entfernen
            cfg['layers'] = {
                k: v for k, v in layers.items()
                if not k.startswith('_') and isinstance(v, dict)
            }
            logger.info('Konfiguration aus %s geladen.', name)
            return cfg
        except (OSError, ValueError) as e:
            logger.error('Konfiguration %s konnte nicht gelesen werden: %s', name, e)
    logger.info('Keine Konfigurationsdatei gefunden, verwende eingebaute Defaults.')
    return DEFAULT_CONFIG


CONFIG = load_config()

PORT = int(CONFIG.get('port', 8080))
_tiles_dir = CONFIG.get('tiles_dir', 'tiles')
TILES_DIR = _tiles_dir if os.path.isabs(_tiles_dir) else os.path.join(ROOT, _tiles_dir)
LAYERS = CONFIG['layers']
MIN_ZOOM = int(CONFIG.get('min_zoom', 8))
LAYER_MAX_ZOOM = {k: int(v.get('max_zoom', 19)) for k, v in LAYERS.items()}
LAYER_MIN_ZOOM = {k: int(v.get('min_zoom', MIN_ZOOM)) for k, v in LAYERS.items()}
DEFAULT_BBOX = tuple(CONFIG.get('default_bbox', [51.2, 6.5, 55.3, 14.6]))  # min_lat, min_lon, max_lat, max_lon
USER_AGENT = CONFIG.get('user_agent', 'LocalTileViewer/1.0')
TILE_PATTERN = re.compile(r'^/tiles/([a-z0-9_]+)/(\d+)/(\d+)/(\d+)\.png$')

R = 6378137.0
ORIGIN_SHIFT = math.pi * R


def lat_lon_to_tile_xy(lat: float, lon: float, z: int):
    n = 1 << z
    x = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y


def tile_range_for_bbox(bbox, z: int):
    nw = lat_lon_to_tile_xy(bbox[2], bbox[1], z)
    se = lat_lon_to_tile_xy(bbox[0], bbox[3], z)
    n = (1 << z) - 1
    x_min = max(0, min(nw[0], se[0]))
    x_max = min(n, max(nw[0], se[0]))
    y_min = max(0, min(nw[1], se[1]))
    y_max = min(n, max(nw[1], se[1]))
    return x_min, x_max, y_min, y_max


def count_cached_tiles(layer: str, z: int, x_min: int, x_max: int, y_min: int, y_max: int) -> int:
    zdir = os.path.join(TILES_DIR, layer, str(z))
    if not os.path.isdir(zdir):
        return 0
    total = 0
    for xdir in os.scandir(zdir):
        if not xdir.is_dir():
            continue
        try:
            x = int(xdir.name)
        except ValueError:
            continue
        if x < x_min or x > x_max:
            continue
        for entry in os.scandir(xdir):
            if not entry.is_file() or not entry.name.endswith('.png'):
                continue
            try:
                y = int(entry.name[:-4])
            except ValueError:
                continue
            if y_min <= y <= y_max:
                total += 1
    return total


def tile_to_bbox(z: int, x: int, y: int):
    """XYZ-Tile-Koordinaten in EPSG:3857-BBOX umrechnen."""
    n = 2 ** z
    res = (2 * math.pi * R) / (256 * n)
    minx = x * 256 * res - ORIGIN_SHIFT
    maxx = (x + 1) * 256 * res - ORIGIN_SHIFT
    maxy = ORIGIN_SHIFT - y * 256 * res
    miny = ORIGIN_SHIFT - (y + 1) * 256 * res
    return (minx, miny, maxx, maxy)


def tile_latlon_bbox(z: int, x: int, y: int):
    """XYZ-Tile-Koordinaten in Lat/Lon-BBOX (s, w, n, e) umrechnen."""
    n = 1 << z
    lon_w = x / n * 360 - 180
    lon_e = (x + 1) / n * 360 - 180
    lat_n = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_s = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return (lat_s, lon_w, lat_n, lon_e)


def tile_covered(layer_cfg: dict, z: int, x: int, y: int) -> bool:
    """True, wenn die Kachel die Layer-BBox schneidet und im Zoom-Bereich liegt."""
    if z < int(layer_cfg.get('min_zoom', MIN_ZOOM)) or z > int(layer_cfg.get('max_zoom', 19)):
        return False
    bbox = layer_cfg.get('bbox')
    if not bbox:
        return True
    s, w, n, e = tile_latlon_bbox(z, x, y)
    return s <= bbox[2] and n >= bbox[0] and w <= bbox[3] and e >= bbox[1]


def png_is_empty(data: bytes) -> bool:
    """Vollständig transparente/uniforme 256er-PNGs sind < 512 Bytes klein."""
    return len(data) < 512


def source_url(layer_cfg: dict, z: int, x: int, y: int) -> str:
    if layer_cfg.get('type') == 'xyz':
        return layer_cfg['url'].format(z=z, x=x, y=y)
    bbox = tile_to_bbox(z, x, y)
    b = ','.join(str(c) for c in bbox)
    transparent = 'true' if layer_cfg.get('transparent', True) else 'false'
    return (
        f"{layer_cfg['base']}SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS={layer_cfg['layer']}&STYLES=&CRS=EPSG:3857"
        f"&BBOX={b}&WIDTH=256&HEIGHT=256&FORMAT=image/png&TRANSPARENT={transparent}"
    )


class TileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        try:
            tile_match = TILE_PATTERN.match(self.path)
            if tile_match:
                layer, z, x, y = tile_match.group(1), int(tile_match.group(2)), int(tile_match.group(3)), int(tile_match.group(4))
                return self.serve_tile(layer, z, x, y)

            if self.path == '/version':
                return self.send_json({'version': VERSION})

            if self.path == '/stats':
                return self.serve_stats()

            if self.path.startswith('/missing'):
                return self.serve_missing()

            if self.path.startswith('/next-missing'):
                return self.serve_next_missing()

            if self.path in ('/', '/index.html'):
                self.path = '/index.html'

            return super().do_GET()
        except ConnectionError:
            pass  # Client hat die Verbindung abgebrochen (z. B. Tile-Request abgebrochen)
        except Exception:
            logger.exception("Unhandled error in do_GET for %s", self.path)
            try:
                self.send_error(500, explain='Interner Serverfehler')
            except ConnectionError:
                pass

    def serve_tile(self, layer: str, z: int, x: int, y: int):
        if layer not in LAYERS:
            self.send_error(404)
            return

        # Kachel außerhalb der Layer-Abdeckung / des Zoom-Bereichs:
        # sofort 404, ohne Upstream-Abruf und ohne Cache-Eintrag.
        if not tile_covered(LAYERS[layer], z, x, y):
            self.send_error(404)
            return

        tile_path = os.path.join(TILES_DIR, layer, str(z), str(x), f'{y}.png')

        # Bereits lokal vorhanden?
        if os.path.exists(tile_path):
            with open(tile_path, 'rb') as f:
                data = f.read()
            self.send_png(data, cached=True)
            return

        # Vom Quellserver holen und speichern
        url = source_url(LAYERS[layer], z, x, y)
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
        except urllib.error.HTTPError as e:
            logger.error("Quellserver HTTP-Fehler %s für %r %s: %s", e.code, layer, (z, x, y), e)
            self.send_error(e.code, explain=str(e))
            return
        except Exception as e:
            logger.error("Quellserver Abruffehler %r %s: %s", layer, (z, x, y), e)
            self.send_error(502, explain=str(e))
            return

        if not data.startswith(b'\x89PNG'):
            logger.error("Quellserver lieferte keine PNG für %r %s", layer, (z, x, y))
            self.send_error(502, explain='Ungültige Antwort vom Server')
            return

        # Vollständig leere (transparente) Kachel -> als fehlend behandeln,
        # damit das Frontend eine gröbere Zoomstufe hochskalieren kann.
        if png_is_empty(data):
            self.send_error(404)
            return

        os.makedirs(os.path.dirname(tile_path), exist_ok=True)
        with open(tile_path, 'wb') as f:
            f.write(data)

        self.send_png(data, cached=False)

    def serve_stats(self):
        result = {}
        for layer, max_z in LAYER_MAX_ZOOM.items():
            bbox = tuple(LAYERS[layer].get('bbox', DEFAULT_BBOX))
            result[layer] = {}
            for z in range(LAYER_MIN_ZOOM.get(layer, MIN_ZOOM), max_z + 1):
                x_min, x_max, y_min, y_max = tile_range_for_bbox(bbox, z)
                total = (x_max - x_min + 1) * (y_max - y_min + 1)
                cached = count_cached_tiles(layer, z, x_min, x_max, y_min, y_max)
                percent = round(cached / total * 100, 2) if total else 0.0
                result[layer][z] = {'total': total, 'cached': cached, 'percent': percent}
        self.send_json(result)

    def send_json(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_missing(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            layer = qs.get('layer', [''])[0]
            z = int(qs.get('z', ['0'])[0])
            xmin = int(qs.get('xmin', ['0'])[0])
            xmax = int(qs.get('xmax', ['0'])[0])
            ymin = int(qs.get('ymin', ['0'])[0])
            ymax = int(qs.get('ymax', ['0'])[0])
        except (ValueError, KeyError):
            self.send_error(400)
            return

        if layer not in LAYERS:
            self.send_error(404)
            return

        missing = []
        for x in range(xmin, xmax + 1):
            for y in range(ymin, ymax + 1):
                tile_path = os.path.join(TILES_DIR, layer, str(z), str(x), f'{y}.png')
                if not os.path.exists(tile_path):
                    missing.append([x, y])
        self.send_json(missing)

    def serve_next_missing(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            layer_list = qs.get('layers', [','.join(LAYERS.keys())])[0].split(',')
            layers = [l for l in layer_list if l in LAYERS]
            if not layers:
                self.send_error(404)
                return
            minZ = int(qs.get('minZ', ['8'])[0])
            maxZ = int(qs.get('maxZ', ['19'])[0])
            bbox_str = qs.get('bbox', [','.join(str(c) for c in DEFAULT_BBOX)])[0]
            bbox = [float(c) for c in bbox_str.split(',')]
        except (ValueError, KeyError):
            self.send_error(400)
            return

        candidates = []
        for layer in layers:
            z_min = LAYER_MIN_ZOOM.get(layer, MIN_ZOOM)
            z_max = LAYER_MAX_ZOOM.get(layer, 19)
            for z in range(minZ, maxZ + 1):
                if z < z_min or z > z_max:
                    continue
                candidates.append((layer, z))
        if not candidates:
            self.send_json({'done': True})
            return

        random.shuffle(candidates)
        for layer, z in candidates:
            x_min, x_max, y_min, y_max = tile_range_for_bbox(bbox, z)
            if x_min > x_max or y_min > y_max:
                continue
            for _ in range(50):
                x = random.randint(x_min, x_max)
                y = random.randint(y_min, y_max)
                tile_path = os.path.join(TILES_DIR, layer, str(z), str(x), f'{y}.png')
                if not os.path.exists(tile_path):
                    self.send_json({'layer': layer, 'z': z, 'x': x, 'y': y})
                    return
        self.send_json({'done': True})

    def do_HEAD(self):
        try:
            tile_match = TILE_PATTERN.match(self.path)
            if tile_match:
                layer, z, x, y = tile_match.group(1), int(tile_match.group(2)), int(tile_match.group(3)), int(tile_match.group(4))
                return self.serve_tile_head(layer, z, x, y)
            return super().do_HEAD()
        except ConnectionError:
            pass
        except Exception:
            logger.exception("Unhandled error in do_HEAD for %s", self.path)
            try:
                self.send_error(500, explain='Interner Serverfehler')
            except ConnectionError:
                pass

    def serve_tile_head(self, layer: str, z: int, x: int, y: int):
        if layer not in LAYERS:
            self.send_error(404)
            return
        tile_path = os.path.join(TILES_DIR, layer, str(z), str(x), f'{y}.png')
        if os.path.exists(tile_path):
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('X-Tile-Cached', 'true')
            self.send_header('Content-Length', str(os.path.getsize(tile_path)))
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def send_png(self, data: bytes, cached: bool = False):
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        if cached:
            self.send_header('X-Tile-Cached', 'true')
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    os.makedirs(TILES_DIR, exist_ok=True)
    logger.info('Tile-Server v%s startet auf http://localhost:%s/', VERSION, PORT)
    logger.info('Kacheln werden unter %s gespeichert.', TILES_DIR)
    try:
        with socketserver.ThreadingTCPServer(('', PORT), TileHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Server beendet.')
