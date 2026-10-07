#!/usr/bin/env python3
"""HTTP-Integrations-Tests: echter Tile-Server auf zufälligem Port mit
temporärem Kachel-Verzeichnis. Upstream-Abrufe werden gemockt; einige Tests
nutzen zusätzlich echte WMS-Dienste (abschaltbar via SKIP_ONLINE=1)."""
import io
import json
import os
import socketserver
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serve  # noqa: E402
import pngutil  # noqa: E402
from pngutil import PNG_REAL, PNG_EMPTY, PNG_WHITE  # noqa: E402

SKIP_ONLINE = os.environ.get('SKIP_ONLINE') == '1'


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


_real_urlopen = urllib.request.urlopen


def fake_urlopen_factory(payload=PNG_REAL):
    """Mockt nur Upstream-Abrufe; localhost-Requests gehen durch."""
    def _fake(req, timeout=30, context=None):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        if '127.0.0.1' in url or 'localhost' in url:
            return _real_urlopen(req, timeout=timeout)
        return FakeResponse(payload)
    return _fake


def fake_urlopen_error_factory():
    def _fake(req, timeout=30, context=None):
        url = req.full_url if hasattr(req, 'full_url') else str(req)
        if '127.0.0.1' in url or 'localhost' in url:
            return _real_urlopen(req, timeout=timeout)
        raise urllib.error.URLError('kaputt')
    return _fake


def upstream_calls(mock_obj):
    """Nur Calls an echte Quellserver (nicht localhost-Testrequests)."""
    return [c for c in mock_obj.call_args_list
            if '127.0.0.1' not in str(c) and 'localhost' not in str(c)]


class ServerFixture(unittest.TestCase):
    """Server auf Port 0 (zufällig), Tiles in tempdir."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._old_tiles = serve.TILES_DIR
        serve.TILES_DIR = cls._tmp.name
        serve.logger.setLevel('CRITICAL')
        cls.httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), serve.TileHandler)
        cls.port = cls.httpd.server_address[1]
        cls._t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls._t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        serve.TILES_DIR = cls._old_tiles
        cls._tmp.cleanup()

    def url(self, path):
        return f'http://127.0.0.1:{self.port}{path}'

    def get(self, path, timeout=15):
        return urllib.request.urlopen(self.url(path), timeout=timeout)

    def get_status(self, path, timeout=15):
        try:
            r = self.get(path, timeout)
            return r.status
        except urllib.error.HTTPError as e:
            return e.code


class TestStaticEndpoints(ServerFixture):
    def test_version(self):
        data = json.loads(self.get('/version').read())
        self.assertRegex(data['version'], r'^\d+\.\d+\.\d+$')
        # Update-Check-Felder vorhanden (latest None, wenn noch nicht
        # geprueft oder offline; nie ein Fehler)
        self.assertIn('latest', data)
        self.assertIn('latest_url', data)
        self.assertIn('repo_url', data)
        self.assertIn('Tile-Caching-and-Offline-Server-Tool-BRD',
                      data['repo_url'])

    def test_version_latest_cached(self):
        """Gepatchter Release-Cache wird über /version ausgespielt."""
        old, old_t = serve.LATEST_RELEASE, serve._LATEST_CHECKED
        try:
            # laufenden Refresh abwarten, damit er den Patch nicht
            # ueberschreibt (Race beim parallelen /version-Aufruf)
            serve._LATEST_DONE.wait(timeout=15)
            serve.LATEST_RELEASE = {'tag': '9.9.9', 'url': 'https://x.test/r'}
            serve._LATEST_CHECKED = time.time()
            data = json.loads(self.get('/version').read())
            self.assertEqual(data['latest'], '9.9.9')
            self.assertEqual(data['latest_url'], 'https://x.test/r')
        finally:
            serve.LATEST_RELEASE, serve._LATEST_CHECKED = old, old_t

    def test_index(self):
        body = self.get('/').read()
        self.assertIn(b'leaflet', body.lower())

    def test_geojson_served(self):
        r = self.get('/data/bundeslaender.geo.json')
        data = json.loads(r.read())
        self.assertEqual(len(data['features']), 16)

    def test_stats_all_layers(self):
        data = json.loads(self.get('/stats').read())
        self.assertEqual(set(data.keys()), set(serve.LAYERS.keys()))
        for lid, zooms in data.items():
            self.assertIsInstance(zooms, dict)
            minz = serve.LAYER_MIN_ZOOM.get(lid, serve.MIN_ZOOM)
            for z in zooms:
                self.assertGreaterEqual(int(z), minz)
                self.assertIn('total', zooms[z])
                self.assertIn('cached', zooms[z])
                self.assertIn('percent', zooms[z])

    def test_missing_endpoint(self):
        data = json.loads(self.get(
            '/missing?layer=dtk5&z=12&xmin=2160&xmax=2161&ymin=1323&ymax=1324').read())
        self.assertEqual(len(data), 4)
        self.assertEqual(sorted(data)[0], [2160, 1323])

    def test_next_missing(self):
        data = json.loads(self.get('/next-missing?layers=osm&minZ=8&maxZ=8').read())
        self.assertTrue('done' in data or 'x' in data)

    def test_next_missing_done_when_out_of_range(self):
        data = json.loads(self.get('/next-missing?layers=osm&minZ=20&maxZ=21').read())
        self.assertTrue(data.get('done'))

    def test_unknown_path(self):
        self.assertIn(self.get_status('/gibts-nicht'), (404, 500))

    def test_unknown_layer_tile(self):
        self.assertEqual(self.get_status('/tiles/xxx/12/1/1.png'), 404)

    def test_index_injects_version(self):
        """index.html wird mit eingesetzter Server-Version ausgeliefert."""
        body = self.get('/').read()
        self.assertNotIn(b'__TILE_SERVER_VERSION__', body)
        self.assertIn(serve.VERSION.encode(), body)


class TestTileServing(ServerFixture):
    """Kachel-Abruf: Cache-Hit, BBox-404, Zoom-404, Mocked-Upstream."""

    def seed_tile(self, layer, z, x, y, payload=PNG_REAL):
        p = os.path.join(serve.TILES_DIR, layer, str(z), str(x))
        os.makedirs(p, exist_ok=True)
        with open(os.path.join(p, f'{y}.png'), 'wb') as f:
            f.write(payload)

    def test_cached_tile_served(self):
        self.seed_tile('osm', 12, 2161, 1324)
        r = self.get('/tiles/osm/12/2161/1324.png')
        self.assertEqual(r.read(), PNG_REAL)
        self.assertEqual(r.headers.get('X-Tile-Cached'), 'true')

    def test_cached_tile_head(self):
        self.seed_tile('osm', 12, 2162, 1324)
        req = urllib.request.Request(self.url('/tiles/osm/12/2162/1324.png'), method='HEAD')
        r = urllib.request.urlopen(req, timeout=10)
        self.assertEqual(r.status, 200)
        self.assertEqual(r.headers.get('X-Tile-Cached'), 'true')

    def test_head_missing_tile(self):
        req = urllib.request.Request(self.url('/tiles/osm/12/2161/1399.png'), method='HEAD')
        try:
            urllib.request.urlopen(req, timeout=10)
            self.fail('erwartete 404')
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_tile_outside_bbox_404_no_fetch(self):
        """hh_dop-Kachel in Rostock-Gebiet -> 404 ohne Upstream-Abruf."""
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory()) as m:
            status = self.get_status('/tiles/hh_dop/12/2185/1325.png')
            self.assertEqual(status, 404)
            self.assertEqual(upstream_calls(m), [])

    def test_tile_below_min_zoom_404(self):
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory()) as m:
            self.assertEqual(self.get_status('/tiles/mv_dtk10/13/8742/5300.png'), 404)
            self.assertEqual(upstream_calls(m), [])

    def test_tile_above_max_zoom_404(self):
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory()) as m:
            self.assertEqual(self.get_status('/tiles/osm/20/1/1.png'), 404)
            self.assertEqual(upstream_calls(m), [])

    def test_upstream_fetch_and_cache(self):
        """Erfolgreicher Upstream-Abruf: 200, PNG, Datei landet im Cache."""
        zxy = '/tiles/ni_dop20/12/2158/1350.png'
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_REAL)) as m:
            r = self.get(zxy)
            self.assertEqual(r.status, 200)
            self.assertEqual(r.read(), PNG_REAL)
            self.assertEqual(len(upstream_calls(m)), 1)
        cached = os.path.join(serve.TILES_DIR, 'ni_dop20', '12', '2158', '1350.png')
        self.assertTrue(os.path.isfile(cached))
        # zweiter Abruf kommt aus dem Cache -> kein Upstream
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory()) as m:
            r2 = self.get(zxy)
            self.assertEqual(r2.headers.get('X-Tile-Cached'), 'true')
            self.assertEqual(upstream_calls(m), [])

    def test_empty_upstream_tile_404_not_cached(self):
        """Transparente Leer-Kachel -> 404, nicht im Cache."""
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_EMPTY)):
            status = self.get_status('/tiles/mv_dop/12/2185/1325.png')
            self.assertEqual(status, 404)
        self.assertFalse(os.path.exists(
            os.path.join(serve.TILES_DIR, 'mv_dop', '12', '2185', '1325.png')))

    def test_white_upstream_tile_404_not_cached(self):
        """Opak-weiße Upstream-Kachel (Dienst ignoriert TRANSPARENT)
        -> ebenfalls 404, nicht im Cache."""
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_WHITE)):
            status = self.get_status('/tiles/mv_dop/12/2186/1324.png')
            self.assertEqual(status, 404)
        self.assertFalse(os.path.exists(
            os.path.join(serve.TILES_DIR, 'mv_dop', '12', '2186', '1324.png')))

    def test_stale_white_cache_tile_selfheals(self):
        """Alte einfarbige Cache-Leiche wird verworfen und neu geladen."""
        self.seed_tile('ni_dop20', 12, 2160, 1350, payload=PNG_WHITE)
        cached = os.path.join(serve.TILES_DIR, 'ni_dop20', '12', '2160', '1350.png')
        self.assertTrue(os.path.isfile(cached))
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_REAL)) as m:
            r = self.get('/tiles/ni_dop20/12/2160/1350.png')
            self.assertEqual(r.status, 200)
            self.assertEqual(r.read(), PNG_REAL)
            # wurde neu vom Upstream geladen (nicht aus dem Cache)
            self.assertEqual(len(upstream_calls(m)), 1)
        self.assertEqual(open(cached, 'rb').read(), PNG_REAL)

    def test_upstream_invalid_png_502(self):
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(b'<html>error</html>' * 100)):
            self.assertEqual(self.get_status('/tiles/mv_dop/12/2186/1325.png'), 502)

    def test_tile_url_with_version_query(self):
        """?v=…-Cache-Buster-Query wird toleriert (gleiche Kachel)."""
        self.seed_tile('osm', 12, 2163, 1324)
        r = self.get('/tiles/osm/12/2163/1324.png?v=999')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.read(), PNG_REAL)

    def test_masked_tile_outside_state_404(self):
        """Kachel in der mv-BBox, aber komplett außerhalb des MV-Polygons
        (Ratzeburg, SH) -> Maske entfernt alles -> 404."""
        # z12 x2170 y1315: Ratzeburg-Gegend — in mv-BBox, nicht im MV-Polygon
        x, y = serve.lat_lon_to_tile_xy(53.7, 10.68, 12)
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_WHITE)):
            self.assertEqual(self.get_status(f'/tiles/mv_dop/12/{x}/{y}.png'), 404)

    def test_masked_edge_tile_keeps_inside(self):
        """Randkachel: außerhalb MV transparent, innerhalb Inhalt."""
        x, y = serve.lat_lon_to_tile_xy(53.87, 10.9, 12)
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_REAL)):
            r = self.get(f'/tiles/mv_dop/12/{x}/{y}.png')
            self.assertEqual(r.status, 200)
            dec = serve.png_decode(r.read())
            self.assertIsNotNone(dec)
            _w, _h, bpp, px = dec
            alphas = {px[i + 3] for i in range(0, len(px), 4)}
            self.assertIn(0, alphas)    # außerhalb transparent
            self.assertIn(255, alphas)  # innerhalb erhalten
        # gecacht: zweite Anfrage ohne Upstream
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_factory(PNG_EMPTY)) as m:
            r2 = self.get(f'/tiles/mv_dop/12/{x}/{y}.png')
            self.assertEqual(r2.status, 200)
            self.assertEqual(upstream_calls(m), [])

    def test_upstream_error_502(self):
        with mock.patch.object(serve.urllib.request, 'urlopen',
                               side_effect=fake_urlopen_error_factory()):
            self.assertEqual(self.get_status('/tiles/mv_dop/12/2187/1325.png'), 502)


@unittest.skipIf(SKIP_ONLINE, 'SKIP_ONLINE=1 gesetzt')
class TestRealUpstream(ServerFixture):
    """Echte Abrufe gegen die Open-Data-WMS (benötigt Internet)."""

    def test_real_ni_dop20(self):
        r = self.get('/tiles/ni_dop20/12/2158/1350.png', timeout=90)
        self.assertEqual(r.status, 200)
        self.assertGreater(len(r.read()), 1000)

    def test_real_hh_dop(self):
        r = self.get('/tiles/hh_dop/12/2161/1324.png', timeout=90)
        self.assertEqual(r.status, 200)

    def test_real_mv_dop(self):
        r = self.get('/tiles/mv_dop/12/2185/1325.png', timeout=90)
        self.assertEqual(r.status, 200)

    def test_real_osm(self):
        r = self.get('/tiles/osm/12/2161/1324.png', timeout=60)
        self.assertEqual(r.status, 200)

    def test_real_sh_dtk5(self):
        r = self.get('/tiles/dtk5/12/2160/1320.png', timeout=90)
        self.assertEqual(r.status, 200)

    def test_real_sh_dop20(self):
        r = self.get('/tiles/dop20/12/2160/1320.png', timeout=90)
        self.assertEqual(r.status, 200)

    def test_real_hh_dop_u(self):
        r = self.get('/tiles/hh_dop_u/12/2161/1324.png', timeout=90)
        self.assertEqual(r.status, 200)

    def test_real_mv_dtk10_z15(self):
        r = self.get('/tiles/mv_dtk10/15/17485/10600.png', timeout=90)
        self.assertEqual(r.status, 200)

    def _check_real(self, layer, lat, lon, z=12):
        """Echte Kachel für Stadtzentrum lat/lon abrufen (Status 200, PNG)."""
        x, y = serve.lat_lon_to_tile_xy(lat, lon, z)
        r = self.get(f'/tiles/{layer}/{z}/{x}/{y}.png', timeout=90)
        self.assertEqual(r.status, 200, f'{layer} z{z}/{x}/{y}')
        self.assertTrue(r.read().startswith(b'\x89PNG'), layer)

    def test_real_bw_dop(self):
        self._check_real('bw_dop', 48.776, 9.183)     # Stuttgart

    def test_real_by_dop(self):
        self._check_real('by_dop', 48.137, 11.576)    # Muenchen

    def test_real_bb_dop(self):
        self._check_real('bb_dop', 52.394, 13.064)    # Potsdam

    def test_real_be_dop(self):
        self._check_real('be_dop', 52.520, 13.405)    # Berlin Mitte

    def test_real_hb_dop(self):
        self._check_real('hb_dop', 53.075, 8.807)     # Bremen

    def test_real_he_dop(self):
        self._check_real('he_dop', 50.110, 8.682)     # Frankfurt

    def test_real_nw_dop(self):
        self._check_real('nw_dop', 51.456, 7.016)     # Wuppertal

    def test_real_rp_dop(self):
        self._check_real('rp_dop', 49.993, 8.271)     # Mainz

    def test_real_sl_dop(self):
        self._check_real('sl_dop', 49.234, 7.000)     # Saarbruecken

    def test_real_sn_dop(self):
        self._check_real('sn_dop', 51.050, 13.737)    # Dresden

    def test_real_st_dop(self):
        self._check_real('st_dop', 52.127, 11.627)    # Magdeburg

    def test_real_th_dop(self):
        self._check_real('th_dop', 50.978, 11.029)    # Erfurt


if __name__ == '__main__':
    unittest.main(verbosity=2)
