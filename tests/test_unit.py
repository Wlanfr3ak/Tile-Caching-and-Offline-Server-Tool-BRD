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


class TestStateMask(unittest.TestCase):
    """mask_png_outside_state: Inhalt außerhalb der Landesgrenze wird
    transparent geschnitten (Wasserzeichen-/Fremdflächen weg)."""

    MV = 'Mecklenburg-Vorpommern'

    def test_polygons_loaded(self):
        self.assertIn(self.MV, serve.STATE_POLYGONS)
        self.assertGreater(len(serve.STATE_POLYGONS[self.MV]), 0)

    def test_fully_inside_passthrough(self):
        # Schwerin z15 liegt komplett innerhalb MV
        x, y = serve.lat_lon_to_tile_xy(53.63, 11.4, 15)
        self.assertIs(
            serve.mask_png_outside_state(pngutil.PNG_WHITE, self.MV, 15, x, y),
            pngutil.PNG_WHITE)

    def test_fully_outside_returns_none(self):
        # Berlin liegt nicht in MV
        x, y = serve.lat_lon_to_tile_xy(52.52, 13.4, 12)
        self.assertIsNone(
            serve.mask_png_outside_state(pngutil.PNG_WHITE, self.MV, 12, x, y))

    def test_edge_tile_masks_alpha(self):
        """Randkachel an der MV-Westgrenze: außen transparent, innen erhalten."""
        x, y = serve.lat_lon_to_tile_xy(53.87, 10.9, 12)
        out = serve.mask_png_outside_state(pngutil.PNG_WHITE, self.MV, 12, x, y)
        self.assertIsInstance(out, bytes)
        w, h, bpp, px = serve.png_decode(out)
        self.assertEqual(bpp, 4)
        n0 = sum(1 for i in range(0, len(px), 4) if px[i + 3] == 0)
        n255 = sum(1 for i in range(0, len(px), 4) if px[i + 3] == 255)
        self.assertGreater(n0, 0)
        self.assertGreater(n255, 0)

    def test_unknown_state_passthrough(self):
        x, y = serve.lat_lon_to_tile_xy(53.63, 11.4, 15)
        self.assertIs(
            serve.mask_png_outside_state(pngutil.PNG_WHITE, 'Atlantis', 15, x, y),
            pngutil.PNG_WHITE)

    def test_masked_output_is_valid_png(self):
        x, y = serve.lat_lon_to_tile_xy(53.87, 10.9, 12)
        out = serve.mask_png_outside_state(pngutil.PNG_REAL, self.MV, 12, x, y)
        self.assertTrue(out.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertIsNotNone(serve.png_decode(out))


def _point_in_rings(lon: float, lat: float, rings: list) -> bool:
    """Ray-Casting mit Paritätsregel — selbe Semantik wie die
    Scanline-Füllung in serve.mask_png_outside_state."""
    xs = []
    for ring in rings:
        m = len(ring)
        for i in range(m):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % m]
            if (y1 <= lat < y2) or (y2 <= lat < y1):
                xs.append(x1 + (lat - y1) * (x2 - x1) / (y2 - y1))
    return sum(1 for x in xs if x > lon) % 2 == 1


class TestStateGeometryCoverage(unittest.TestCase):
    """Pflicht-Orte müssen innerhalb ihrer Landesgeometrie liegen —
    insbesondere Exklaven und Inseln (fingen früher leise raus:
    Bremerhaven fehlte komplett, Büsingen/Neuwerk lagen außerhalb der
    zu grob vereinfachten Polygone des alten Datensatzes)."""

    # (Bundesland, lon, lat, Ortsname)
    COVERAGE_POINTS = [
        ('Baden-Württemberg', 9.183, 48.776, 'Stuttgart'),
        ('Baden-Württemberg', 8.689, 47.697, 'Büsingen (Exklave in CH)'),
        ('Bayern', 11.576, 48.137, 'München'),
        ('Berlin', 13.405, 52.520, 'Berlin-Mitte'),
        ('Brandenburg', 13.064, 52.394, 'Potsdam'),
        ('Bremen', 8.807, 53.075, 'Bremen-Stadt'),
        ('Bremen', 8.580, 53.539, 'Bremerhaven'),
        ('Hamburg', 9.990, 53.550, 'Hamburg-Mitte'),
        ('Hamburg', 8.496, 53.916, 'Neuwerk (Exklave)'),
        ('Hamburg', 8.445, 53.959, 'Scharhörn (Exklave)'),
        ('Hessen', 8.682, 50.110, 'Frankfurt'),
        ('Mecklenburg-Vorpommern', 11.400, 53.630, 'Schwerin'),
        ('Mecklenburg-Vorpommern', 13.400, 54.420, 'Rügen'),
        ('Mecklenburg-Vorpommern', 13.124, 54.567, 'Hiddensee-Vitte'),
        ('Mecklenburg-Vorpommern', 11.430, 53.990, 'Poel'),
        ('Mecklenburg-Vorpommern', 13.910, 54.030, 'Greifswalder Oie'),
        ('Niedersachsen', 9.740, 52.370, 'Hannover'),
        ('Niedersachsen', 6.670, 53.588, 'Borkum'),
        ('Niedersachsen', 6.998, 53.678, 'Juist'),
        ('Niedersachsen', 6.917, 53.672, 'Memmert'),
        ('Niedersachsen', 7.149, 53.713, 'Norderney'),
        ('Niedersachsen', 7.400, 53.725, 'Baltrum'),
        ('Niedersachsen', 7.475, 53.747, 'Langeoog'),
        ('Niedersachsen', 7.750, 53.770, 'Spiekeroog'),
        ('Niedersachsen', 7.905, 53.790, 'Wangerooge'),
        ('Niedersachsen', 8.170, 53.717, 'Mellum'),
        ('Niedersachsen', 8.166, 53.763, 'Langlütjen I'),
        ('Nordrhein-Westfalen', 7.016, 51.456, 'Wuppertal'),
        ('Rheinland-Pfalz', 8.271, 49.993, 'Mainz'),
        ('Saarland', 7.000, 49.234, 'Saarbrücken'),
        ('Sachsen', 13.737, 51.050, 'Dresden'),
        ('Sachsen-Anhalt', 11.627, 52.127, 'Magdeburg'),
        ('Schleswig-Holstein', 7.890, 54.182, 'Helgoland'),
        ('Schleswig-Holstein', 8.310, 54.910, 'Sylt'),
        ('Schleswig-Holstein', 8.500, 54.720, 'Föhr'),
        ('Schleswig-Holstein', 8.355, 54.648, 'Amrum'),
        ('Schleswig-Holstein', 8.630, 54.520, 'Pellworm'),
        ('Schleswig-Holstein', 8.550, 54.570, 'Hallig Hooge'),
        ('Schleswig-Holstein', 11.134, 54.474, 'Fehmarn'),
        ('Thüringen', 11.029, 50.978, 'Erfurt'),
    ]

    def test_all_required_points_inside(self):
        fails = []
        for state, lon, lat, name in self.COVERAGE_POINTS:
            rings = serve.STATE_POLYGONS.get(state)
            self.assertIsNotNone(rings, f'Land {state} fehlt in STATE_POLYGONS')
            if not _point_in_rings(lon, lat, rings):
                fails.append(f'{name} ({lat}, {lon}) nicht in {state}')
        self.assertEqual(fails, [], 'Orte außerhalb ihrer Landesgeometrie:\n  '
                         + '\n  '.join(fails))

    def test_outside_points_rejected(self):
        """Negativ-Punkte: klare Auslandspunkte dürfen nicht drin liegen."""
        for state, lon, lat, name in [
            ('Mecklenburg-Vorpommern', 12.57, 55.68, 'Kopenhagen'),
            ('Baden-Württemberg', 7.59, 47.56, 'Basel'),
            ('Bayern', 14.29, 48.30, 'Linz'),
        ]:
            self.assertFalse(
                _point_in_rings(lon, lat, serve.STATE_POLYGONS[state]),
                f'{name} fälschlich in {state}')

    def test_all_masks_have_geometry(self):
        """Jeder mask-Wert in den Layer-Configs muss eine Geometrie haben."""
        for lid, cfg in serve.LAYERS.items():
            mask = cfg.get('mask')
            if mask:
                self.assertIn(mask, serve.STATE_POLYGONS,
                              f'{lid}: mask "{mask}" ohne Geometrie')


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
                    'mv_dop', 'mv_dtk10', 'bw_dop', 'by_dop', 'bb_dop',
                    'be_dop', 'hb_dop', 'he_dop', 'nw_dop', 'rp_dop',
                    'sl_dop', 'sn_dop', 'st_dop', 'th_dop', 'osm'):
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
