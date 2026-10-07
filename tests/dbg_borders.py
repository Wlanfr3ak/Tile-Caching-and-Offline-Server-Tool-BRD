import os, sys, tempfile, threading, socketserver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import serve
from playwright.sync_api import sync_playwright

tmp = tempfile.TemporaryDirectory()
serve.TILES_DIR = tmp.name
httpd = socketserver.ThreadingTCPServer(('127.0.0.1', 0), serve.TileHandler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.on('pageerror', lambda e: print('[pageerror]', e))
    pg.goto(f'http://127.0.0.1:{port}/')
    pg.wait_for_selector('canvas.leaflet-tile', timeout=30000)
    pg.check('#cb-borders')
    pg.wait_for_timeout(3000)
    info = pg.evaluate("""() => {
      const pane = document.querySelector('.leaflet-border-pane');
      const paths = [...document.querySelectorAll('.leaflet-border-pane path')];
      const groups = [...document.querySelectorAll('.leaflet-pane svg g')];
      return {
        paneExists: !!pane,
        paneChildren: pane ? pane.children.length : -1,
        svgInPane: pane ? pane.querySelectorAll('svg').length : -1,
        allPaneSvgs: groups.length,
        pathCount: paths.length,
        dLens: paths.map(p => (p.getAttribute('d')||'').length),
        strokes: paths.slice(0,20).map(p => p.getAttribute('stroke')),
      };
    }""")
    print(info)
    pg.screenshot(path='tests/out/dbg_borders.png')
    b.close()
httpd.shutdown()
