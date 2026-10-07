#!/usr/bin/env python3
"""Unit-Tests für die reinen Funktionen von serve.py (kein Netzwerk nötig)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serve  # noqa: E402
import pngutil  # noqa: E402


class TestTileMath(unittest.TestCase):
    """Kachel-Koordinaten-Mathematik (XYZ <-> LatLon <-> EPSG:3857)."""

    def test_z0_origin(self):
        x, y = serve.lat_lon_to_tile_xy(0.0, 0.0, 0)
        self.assertEqual((x, y), (0, 0))

    def test_z1_center(self):
        x, y = serve.lat_lon_to_tile_xy(0.0, 0.0, 1)
        self.assertEqual((x, y), (1, 1))

    def test_z1_corners(self):
        self.assertEqual(serve.lat_lon_to_tile_xy(85.0, -179.9, 1), (0, 0))
        self.assertEqual(serve.lat_lon_to_tile_xy(-85.0, 179.9, 1), (1, 1))

    def test_hamburg_z12(self):
        x, y = serve.lat_lon_to_tile_xy(53.55, 9.99, 12)
        self.assertEqual((x, y), (2161, 1323))

    def test_tile_range_for_bbox(self):
        # Hamburg-Kachel (2161,1323) muss in der SH-BBox-Range liegen
        x_min, x_max, y_min, y_max = serve.tile_range_for_bbox((53.3, 7.8, 55.2, 11.5), 12)
        self.assertLessEqual(x_min, 2161)
        self.assertLessEqual(2161, x_max)
        self.assertLessEqual(y_min, 1323)
        self.assertLessEqual(1323, y_max)
        self.assertGreater(x_max, x_min)
        self.assertGreater(y_max, y_min)

    def test_tile_to_bbox_epsg3857(self):
        minx, miny, maxx, maxy = serve.tile_to_bbox(0, 0, 0)
        self.assertAlmostEqual(minx, -serve.ORIGIN_SHIFT)
        self.assertAlmostEqual(maxx, serve.ORIGIN_SHIFT)
        self.assertAlmostEqual(miny, -serve.ORIGIN_SHIFT)
        self.assertAlmostEqual(maxy, serve.ORIGIN_SHIFT)

    def test_tile_latlon_bbox_roundtrip(self):
        z, x, y = 12, 2161, 1324
        s, w, n, e = serve.tile_latlon_bbox(z, x, y)
        cx, cy = serve.lat_lon_to_tile_xy((s + n) / 2, (w + e) / 2, z)
        self.assertEqual((cx, cy), (x, y))


class TestTileCovered(unittest.TestCase):
    """Abdeckungs-/Zoom-Prüfung pro Layer."""

    def setUp(self):
        self.hh = serve.LAYERS['hh_dop']
        self.mv_dtk = serve.LAYERS['mv_dtk10']
        self.osm = serve.LAYERS['osm']

    def test_inside_bbox(self):
        # Hamburg Zentrum z12
        self.assertTrue(serve.tile_covered(self.hh, 12, 2161, 1324))

    def test_outside_bbox(self):
        # Rostock z12 — außerhalb der HH-BBox
        self.assertFalse(serve.tile_covered(self.hh, 12, 2185, 1325))

    def test_below_min_zoom(self):
        # mv_dtk10 hat min_zoom 15
        self.assertFalse(serve.tile_covered(self.mv_dtk, 14, 17485, 10600))
        self.assertTrue(serve.tile_covered(self.mv_dtk, 15, 17485, 10600))

    def test_above_max_zoom(self):
        self.assertFalse(serve.tile_covered(self.osm, 20, 0, 0))

    def test_no_bbox_layer_always_covered(self):
        self.assertTrue(serve.tile_covered({'type': 'wms', 'max_zoom': 19}, 10, 0, 0))


class TestPngIsEmpty(unittest.TestCase):
    """png_is_empty erkennt einfarbige PNGs (transparent ODER opak weiß)
    durch echtes Dekodieren — nicht über die Dateigröße."""

    def test_uniform_white_is_empty(self):
        # opak weiß 256x256 — wie die alten Cache-Leichen (~755 B)
        self.assertTrue(serve.png_is_empty(pngutil.PNG_WHITE))

    def test_uniform_transparent_is_empty(self):
        self.assertTrue(serve.png_is_empty(pngutil.PNG_EMPTY))

    def test_uniform_black_is_empty(self):
        self.assertTrue(serve.png_is_empty(
            pngutil.make_png(pixel=(0, 0, 0, 255))))

    def test_varied_not_empty(self):
        self.assertFalse(serve.png_is_empty(pngutil.PNG_REAL))

    def test_invalid_data_not_empty(self):
        # kaputte/ungültige Daten gelten nicht als 'leer' (Fehlerpfad 502)
        self.assertFalse(serve.png_is_empty(b'\x89PNG' + b'0' * 300))
        self.assertFalse(serve.png_is_empty(b'gar kein PNG'))

    def test_big_not_empty(self):
        # >64KiB kann nicht einfarbig sein -> Früh-Exit ohne Dekodieren
        self.assertFalse(serve.png_is_empty(b'\x89PNG\r\n\x1a\n' + b'0' * 70000))


class TestSourceUrl(unittest.TestCase):
    def test_wms_url(self):
        url = serve.source_url(
            {'type': 'wms', 'base': 'https://x.de/wms?', 'layer': 'l1'},
            12, 2161, 1324)
        self.assertIn('SERVICE=WMS', url)
        self.assertIn('REQUEST=GetMap', url)
        self.assertIn('VERSION=1.3.0', url)
        self.assertIn('LAYERS=l1', url)
        self.assertIn('CRS=EPSG:3857', url)
        self.assertIn('TRANSPARENT=true', url)
        self.assertIn('WIDTH=256', url)
        self.assertIn('HEIGHT=256', url)

    def test_wms_url_transparent_off(self):
        url = serve.source_url(
            {'type': 'wms', 'base': 'https://x.de/wms?', 'layer': 'l1',
             'transparent': False}, 12, 0, 0)
        self.assertIn('TRANSPARENT=false', url)

    def test_xyz_url(self):
        url = serve.source_url(
            {'type': 'xyz', 'url': 'https://t/{z}/{x}/{y}.png'}, 5, 17, 9)
        self.assertEqual(url, 'https://t/5/17/9.png')


class TestCountCachedTiles(unittest.TestCase):
    def test_counts_only_in_range(self):
        with tempfile.TemporaryDirectory() as td:
            old = serve.TILES_DIR
            serve.TILES_DIR = td
            try:
                # 2 Kacheln im Bereich, 1 außerhalb (y), 1 mit Müll-Name
                d = os.path.join(td, 'l1', '10', '100')
                os.makedirs(d)
                for y in ('50', '51', '99'):
                    open(os.path.join(d, f'{y}.png'), 'wb').write(b'x' * 900)
                open(os.path.join(d, 'junk.png'), 'wb').write(b'x')
                n = serve.count_cached_tiles('l1', 10, 100, 100, 50, 51)
                self.assertEqual(n, 2)
            finally:
                serve.TILES_DIR = old

    def test_missing_dir(self):
        self.assertEqual(serve.count_cached_tiles('nonexistent', 10, 0, 1, 0, 1), 0)


class TestLoadConfig(unittest.TestCase):
    def test_layers_present(self):
        for lid in ('dtk5', 'dop20', 'ni_dop20', 'hh_dop', 'hh_dop_u',
                    'mv_dop', 'mv_dtk10', 'osm'):
            self.assertIn(lid, serve.LAYERS, f'Layer {lid} fehlt')

    def test_no_meta_keys(self):
        self.assertNotIn('_schema', serve.LAYERS)

    def test_layer_zoom_maps(self):
        self.assertEqual(serve.LAYER_MAX_ZOOM['mv_dtk10'], 18)
        self.assertEqual(serve.LAYER_MIN_ZOOM['mv_dtk10'], 15)
        self.assertEqual(serve.LAYER_MIN_ZOOM['dtk5'], 8)

    def test_version_loaded(self):
        self.assertRegex(serve.VERSION, r'^\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main(verbosity=2)
