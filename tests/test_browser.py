#!/usr/bin/env python3
"""Browser-Tests mit Playwright (Chromium headless).

Prüft das Frontend inkl. Tile-Laden, Zoom-Fallback, parallele Layer und
Grenzen-Overlay gegen einen echten lokalen Server (temporärer Kachel-Cache,
zufälliger Port). Ausführliches Debug-Logging aller Netzwerk-Requests.

Start:  python tests/test_browser.py        (benötigt: pip install playwright,
                                             python -m playwright install chromium)
"""
import json
import os
import re
import socketserver
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import serve  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

TILE_RE = re.compile(r'/tiles/([a-z0-9_]+)/(\d+)/(\d+)/(\d+)\.png')

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')


class BrowserFixture(unittest.TestCase):
    """Ein Server + ein Browser für die ganze Testklasse."""

    @classmethod
    def setUpClass(cls):
        if sync_playwright is None:
            raise unittest.SkipTest('playwright nicht installiert')

        cls._tmp = tempfile.TemporaryDirectory()
        cls._old_tiles = serve.TILES_DIR
        serve.TILES_DIR = cls._tmp.name
        serve.logger.setLevel('WARNING')
        cls.httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), serve.TileHandler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

        os.makedirs(OUT_DIR, exist_ok=True)
        cls.requests = []   # (methode, url, status)
        cls.console = []    # (level, text)
        cls.page_errors = []

        cls._pw = sync_playwright().start()
        cls.browser = cls._pw.chromium.launch()
        cls.page = cls.browser.new_page(viewport={'width': 1400, 'height': 900})
        cls.page.on('response', cls._on_response)
        cls.page.on('console', lambda m: cls.console.append((m.type, m.text)))
        cls.page.on('pageerror', lambda e: cls.page_errors.append(str(e)))

        print(f'\n[setup] Server auf Port {cls.port}, Cache: {cls._tmp.name}')
        cls.page.goto(f'http://127.0.0.1:{cls.port}/')
        cls.page.wait_for_selector('canvas.leaflet-tile', timeout=30000)
        print('[setup] Seite geladen, erste Kacheln da')

    @classmethod
    def tearDownClass(cls):
        cls.page.screenshot(path=os.path.join(OUT_DIR, 'final_state.png'), full_page=True)
        cls.browser.close()
        cls._pw.stop()
        cls.httpd.shutdown()
        cls.httpd.server_close()
        serve.TILES_DIR = cls._old_tiles
        cls._tmp.cleanup()
        print(f'[teardown] Screenshot: {os.path.join(OUT_DIR, "final_state.png")}')

    @classmethod
    def _on_response(cls, r):
        m = TILE_RE.search(r.url)
        if m:
            cls.requests.append((r.request.method, m.group(0), r.status,
                                 m.group(1), int(m.group(2))))
            print(f'  [net] {r.status} {m.group(0)}')
        else:
            cls.requests.append((r.request.method, r.url, r.status, None, None))

    # ---- Helfer -------------------------------------------------------------

    def tile_requests(self, layer=None, zoom=None):
        return [r for r in self.requests
                if r[3] and (layer is None or r[3] == layer)
                and (zoom is None or r[4] == zoom)]

    def canvas_stats(self, layer_idx=None):
        """Zählt gezeichnete (nicht-transparente) Pixel der Tile-Canvases."""
        return self.page.evaluate("""() => {
          const cs = [...document.querySelectorAll('.leaflet-tile-pane canvas')];
          return cs.map(c => {
            const d = c.getContext('2d').getImageData(0, 0, 256, 256).data;
            let n = 0;
            for (let i = 3; i < d.length; i += 160) if (d[i] > 0) n++;
            return n;
          });
        }""")

    def wait_settled(self, ms=2500):
        self.page.wait_for_timeout(ms)

    def screenshot(self, name):
        self.page.screenshot(path=os.path.join(OUT_DIR, f'{name}.png'), full_page=True)


class TestPageLoad(BrowserFixture):
    def test_01_title(self):
        self.assertIn('Tile-Caching', self.page.title())

    def test_02_leaflet_init(self):
        self.assertTrue(self.page.evaluate("!!window.L"))
        self.assertTrue(self.page.evaluate("!!window.map"))
        self.assertGreater(self.page.locator('.leaflet-container').count(), 0)

    def test_03_layer_ui_built(self):
        self.assertEqual(self.page.locator('#base-layers input[type=checkbox]').count(),
                         len(serve.LAYERS))
        self.assertEqual(self.page.locator('#dl-layers input[type=checkbox]').count(),
                         len(serve.LAYERS))
        self.assertEqual(self.page.locator('#stats-head th').count(),
                         len(serve.LAYERS) + 1)
        self.assertEqual(self.page.locator('#layer-status > div').count(),
                         len(serve.LAYERS))

    def test_04_tiles_are_canvases(self):
        n = self.page.locator('.leaflet-tile-pane canvas').count()
        print(f'  [dom] {n} Canvas-Kacheln')
        self.assertGreater(n, 0)

    def test_05_dtk5_tiles_have_content(self):
        stats = self.canvas_stats()
        print(f'  [px] nicht-leere Pixel pro Canvas: {stats}')
        self.assertTrue(any(s > 0 for s in stats), 'Alle Kacheln leer!')

    def test_06_tile_requests_200(self):
        reqs = self.tile_requests(layer='dtk5')
        oks = [r for r in reqs if r[2] == 200]
        print(f'  [net] dtk5: {len(oks)}/{len(reqs)} Requests 200')
        self.assertGreater(len(oks), 0)

    def test_07_stats_table_filled(self):
        self.page.wait_for_selector('#stats-table tbody tr', state='attached',
                                    timeout=15000)
        n = self.page.locator('#stats-table tbody tr').count()
        print(f'  [dom] Stats-Zeilen: {n}')
        self.assertGreater(n, 0)

    def test_08_no_console_errors(self):
        # 404-Ressourcen-Meldungen sind erwartetes Fallback-Verhalten
        errs = [(t, x) for t, x in self.console
                if t == 'error' and 'favicon' not in x
                and 'Failed to load resource' not in x]
        errs += [('pageerror', e) for e in self.page_errors]
        for t, x in errs:
            print(f'  [console-{t}] {x}')
        self.assertEqual(errs, [])


class TestParallelLayers(BrowserFixture):
    def test_10_enable_second_layer(self):
        self.requests.clear()
        self.page.check('#bl-dop20')
        self.wait_settled()
        dop = self.tile_requests(layer='dop20')
        dtk = self.tile_requests(layer='dtk5')
        print(f'  [net] dop20={len(dop)} dtk5={len(dtk)} Requests parallel')
        self.assertGreater(len(dop), 0)
        stats = self.canvas_stats()
        self.assertTrue(any(s > 0 for s in stats))
        self.screenshot('parallel_dop20')

    def test_11_enable_third_layer(self):
        self.requests.clear()
        self.page.check('#bl-ni_dop20')
        self.wait_settled()
        ni = self.tile_requests(layer='ni_dop20')
        print(f'  [net] ni_dop20={len(ni)} Requests')
        self.assertGreater(len(ni), 0)


class TestZoomFallback(BrowserFixture):
    def test_20_parent_fallback_on_404(self):
        """hh_dop außerhalb der HH-BBox -> 404 -> Fallback auf Eltern-Kacheln."""
        self.requests.clear()
        # Blick auf MV (außerhalb Hamburg), hh_dop einschalten
        self.page.evaluate("map.setView([54.0, 12.1], 12)")
        self.page.check('#bl-hh_dop')
        self.wait_settled(4000)
        reqs = self.tile_requests(layer='hh_dop')
        z12 = [r for r in reqs if r[4] == 12]
        other_z = [r for r in reqs if r[4] != 12]
        zooms = sorted({r[4] for r in reqs})
        print(f'  [fallback] hh_dop-Requests Zooms: {zooms} '
              f'(z12: {len(z12)}, andere: {len(other_z)})')
        self.assertGreater(len(z12), 0, 'keine z12-Anfragen gesehen')
        self.assertGreater(len(other_z), 0,
                           'kein Fallback: nur z12 angefragt, keine Eltern/Kinder')
        self.screenshot('fallback_hh_mv')

    def test_21_child_fallback_draws_content(self):
        """mv_dtk10 bei z13 (unter min_zoom 15): Kinder-Fallback z14+ zeichnet
        echte Inhalte auf die Canvas-Kacheln (Topographie ist in MV vorhanden)."""
        # andere Layer abwählen, damit nur mv_dtk10 anfragt (schnell & isoliert)
        for lid in ('dtk5', 'dop20', 'ni_dop20', 'hh_dop'):
            box = self.page.locator(f'#bl-{lid}')
            if box.is_checked():
                box.uncheck()
        self.requests.clear()
        self.page.evaluate("map.setView([54.09, 12.1], 13)")
        self.page.check('#bl-mv_dtk10')
        self.wait_settled(8000)
        reqs = self.tile_requests(layer='mv_dtk10')
        zooms = sorted({r[4] for r in reqs})
        print(f'  [fallback] mv_dtk10 Zooms: {zooms}')
        self.assertTrue(any(z > 13 for z in zooms),
                        f'kein Kinder-Fallback sichtbar: {zooms}')
        stats = self.canvas_stats()
        print(f'  [px] {stats}')
        self.assertTrue(any(s > 0 for s in stats),
                        'Kinder-Fallback hat keine Inhalte gezeichnet')
        self.screenshot('fallback_mv_dtk10')


class TestBorderOverlay(BrowserFixture):
    def test_30_borders_on(self):
        # Grenzen sind seit v1.6.0 fest eingeblendet (kein Toggle mehr)
        # 'attached' statt 'visible': Leaflet clipt offscreen-Polygone
        # (d="M0 0" -> nie sichtbar -> Timeout bei default 'visible')
        self.page.wait_for_selector('.leaflet-border-pane svg path',
                                    state='attached', timeout=15000)
        paths = self.page.locator('.leaflet-border-pane path')
        n = paths.count()
        strokes = [paths.nth(i).get_attribute('stroke') for i in range(min(n, 100))]
        reds = [s for s in strokes if s == '#d02020']
        blues = [s for s in strokes if s == '#2050d0']
        drawn = self.page.evaluate(
            "[...document.querySelectorAll('.leaflet-border-pane path')]"
            ".filter(p => (p.getAttribute('d') || '').length > 10).length")
        print(f'  [svg] {n} Pfade ({drawn} mit Geometrie), '
              f'rot={len(reds)}, blau={len(blues)}')
        self.assertGreaterEqual(len(reds), 16)   # 16 Bundesländer
        self.assertGreaterEqual(len(blues), 1)   # Staatsgrenze
        self.assertGreater(drawn, 0)             # mindestens einer im View
        self.screenshot('borders')

    def test_31_border_pane_on_top(self):
        z = self.page.evaluate(
            "getComputedStyle(document.querySelector('.leaflet-border-pane')).zIndex")
        self.assertEqual(z, '700')

    def test_32_borders_always_on(self):
        """Grenz-Checkbox ist entfernt - Grenzen bleiben permanent."""
        self.assertEqual(self.page.locator('#cb-borders').count(), 0)
        n = self.page.locator('.leaflet-border-pane path').count()
        self.assertGreaterEqual(n, 17)  # 16 Laender + Staatsgrenze
        self.screenshot('borders_always_on')


class TestVersionBadge(BrowserFixture):
    def test_38_version_badge(self):
        """Versionsnummer wird oben links in der Sidebar angezeigt."""
        el = self.page.locator('#version-badge')
        el.wait_for(state='attached', timeout=5000)
        txt = el.text_content()
        print(f'  [dom] version-badge: {txt!r}')
        self.assertIn(serve.VERSION, txt)
        box = el.bounding_box()
        self.assertIsNotNone(box)
        self.assertLess(box['x'], 320)   # im linken Sidebar-Bereich
        self.assertLess(box['y'], 100)   # ganz oben
        self.screenshot('version_badge')


class TestWorldBasemap(BrowserFixture):
    """Grobe Weltgrundkarte (Länder-Polygone + Namen) unter den Kacheln."""

    def test_35_world_polygons_present(self):
        # z8-Sicht: Welt-Polygone im eigenen Pane unter den Kacheln
        self.page.wait_for_selector('.leaflet-world-pane svg path',
                                    state='attached', timeout=15000)
        n = self.page.locator('.leaflet-world-pane path').count()
        drawn = self.page.evaluate(
            "[...document.querySelectorAll('.leaflet-world-pane path')]"
            ".filter(p => (p.getAttribute('d') || '').length > 10).length")
        z = self.page.evaluate(
            "getComputedStyle(document.querySelector('.leaflet-world-pane')).zIndex")
        fill = self.page.evaluate(
            "document.querySelector('.leaflet-world-pane path')"
            ".getAttribute('fill')")
        print(f'  [svg] {n} Welt-Pfade ({drawn} gezeichnet), zIndex={z}, fill={fill}')
        self.assertGreaterEqual(n, 150)          # ~180 Länder
        self.assertGreater(drawn, 0)
        self.assertEqual(fill, '#ece7d8')
        self.assertLess(int(z), 200)             # unter tilePane (200)

    def test_36_country_labels_low_zoom(self):
        # Auf Zoom 4 (unter Kachel-minZoom 8) müssen Ländernamen erscheinen
        self.page.evaluate("map.setView([51, 10], 4)")
        self.wait_settled(1500)
        labels = self.page.locator('.wlbl')
        n = labels.count()
        texts = [labels.nth(i).text_content() for i in range(min(n, 200))]
        print(f'  [labels] {n} Ländernamen, z.B.: {texts[:8]}')
        self.assertGreater(n, 100)
        self.assertIn('Germany', texts)
        self.screenshot('world_basemap')

    def test_37_world_toggle_and_ocean(self):
        bg = self.page.evaluate(
            "getComputedStyle(document.querySelector('.leaflet-container')).backgroundColor")
        print(f'  [css] Karten-Hintergrund: {bg}')
        self.assertEqual(bg, 'rgb(184, 207, 224)')   # #b8cfe0
        # Toggle aus -> Pane-Pfade + Labels weg
        self.page.uncheck('#cb-world')
        self.wait_settled(800)
        n = self.page.locator('.leaflet-world-pane path').count()
        lbl = self.page.locator('.wlbl').count()
        print(f'  [dom] nach Toggle: {n} Pfade, {lbl} Labels')
        self.assertEqual(n, 0)
        self.assertEqual(lbl, 0)
        self.page.check('#cb-world')


class TestInteraction(BrowserFixture):
    def test_40_map_click_adds_point(self):
        self.page.mouse.click(900, 450)
        self.wait_settled(500)
        items = self.page.locator('#points-list .point-item')
        self.assertGreater(items.count(), 0)
        print(f'  [dom] Punkte: {items.count()}')

    def test_41_zoom_status_updates(self):
        self.page.evaluate("map.setView([54.09, 12.1], 16)")
        self.wait_settled(1200)
        txt = self.page.locator('#mv_dtk10-status').text_content()
        print(f'  [status] mv_dtk10 @z16: {txt}')
        self.assertIn('verfügbar', txt)
        self.page.evaluate("map.setView([54.09, 12.1], 10)")
        self.wait_settled(1200)
        txt_low = self.page.locator('#mv_dtk10-status').text_content()
        print(f'  [status] mv_dtk10 @z10: {txt_low}')
        self.assertIn('nicht', txt_low)

    def test_42_zoom_level_display(self):
        z = self.page.evaluate("map.getZoom()")
        shown = self.page.locator('#zoom-level').text_content()
        self.assertEqual(shown.strip(), str(z))


if __name__ == '__main__':
    unittest.main(verbosity=2)
