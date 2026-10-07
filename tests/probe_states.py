# -*- coding: utf-8 -*-
"""Recherche-Probe: GetCapabilities + GetMap fuer alle neuen Landes-DOP-Dienste."""
import re
import sys
import urllib.request
import urllib.error

sys.path.insert(0, ".")
from serve import tile_to_bbox, lat_lon_to_tile_xy, png_decode

UA = {"User-Agent": "TileCache-Probe/1.0"}

CANDIDATES = {
    "by_dop": ("https://geoservices.bayern.de/od/wms/dop/v1/dop20?", None),
    "bw_dop": ("https://owsproxy.lgl-bw.de/owsproxy/ows/WMS_LGL-BW_ATKIS_DOP_20_C?", None),
    "bb_dop": ("https://isk.geobasis-bb.de/mapproxy/dop20c/service/wms?", None),
    "be_dop": ("https://fbinter.stadt-berlin.de/fb/wms/senstadt/k_luftbild2025?", None),
    "hb_dop": ("https://geodienste.bremen.de/wms_dop_lb?", None),
    "he_dop": ("https://www.geoportal.hessen.de/mapbender/php/wms.php?layer_id=54936&withChilds=1&", None),
    "nw_dop": ("https://www.wms.nrw.de/geobasis/wms_nw_dop?", None),
    "rp_dop": ("https://geo4.service24.rlp.de/wms/rp_dop20.fcgi?", None),
    "sl_dop": ("https://geoportal.saarland.de/mapbender/php/wms.php?inspire=1&layer_id=43492&withChilds=1&", None),
    "sn_dop": ("https://geodienste.sachsen.de/wms_geosn_dop-rgb/guest?", None),
    "st_dop": ("https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest?", None),
    "th_dop": ("https://www.geoproxy.geoportal-th.de/geoproxy/services/DOP20?", None),
}

# repraesentative Orte (lon, lat) je Land
SPOTS = {
    "by_dop": (11.576, 48.137),   # Muenchen
    "bw_dop": (9.183, 48.776),    # Stuttgart
    "bb_dop": (13.900, 51.800),   # Brandenburg Land
    "be_dop": (13.405, 52.520),   # Berlin Mitte
    "hb_dop": (8.807, 53.075),    # Bremen
    "he_dop": (8.682, 50.110),    # Frankfurt
    "nw_dop": (7.016, 51.456),    # Wuppertal (NRW-Sued)
    "rp_dop": (8.271, 49.993),    # Mainz
    "sl_dop": (7.000, 49.234),    # Saarbruecken
    "sn_dop": (13.737, 51.050),   # Dresden
    "st_dop": (11.627, 52.127),   # Magdeburg
    "th_dop": (10.700, 50.978),   # Arnstadt/Erfurt
}


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def caps(base):
    try:
        data = get(base + "SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0")
    except Exception as e:
        return None, f"caps FAIL: {e}"
    txt = data.decode("utf-8", "replace")
    layers = re.findall(r"<Layer[^>]*>.*?<Name>([^<]+)</Name>", txt, re.S)
    has3857 = "EPSG:3857" in txt or "CRS:84" in txt
    return (layers, has3857), None


def pick_layer(layers):
    for pat in (r"dop.*(?:rgb|farbe|c$|20$|020)", r"dop", r"luftbild", r"ortho"):
        for ln in layers:
            if re.search(pat, ln.lower()) and "info" not in ln.lower():
                return ln
    return layers[-1] if layers else None


def try_map(base, layer, lon, lat):
    z = 15
    x, y = lat_lon_to_tile_xy(lat, lon, z)
    w, s, e, n = tile_to_bbox(z, x, y)
    url = (f"{base}SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={layer}"
           f"&STYLES=&CRS=EPSG:3857&BBOX={w},{s},{e},{n}&WIDTH=256&HEIGHT=256"
           f"&FORMAT=image/png&TRANSPARENT=true")
    try:
        data = get(url)
    except Exception as e:
        return f"GetMap FAIL: {e}"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        dec = png_decode(data)
        if dec:
            pw, ph, bpp, px = dec
            opaque = sum(1 for i in range(3, len(px), bpp) if px[i] > 0) if bpp == 4 else -1
            return f"OK {len(data)}B {pw}x{ph} bpp={bpp} opaque={opaque}"
        return f"OK {len(data)}B (decode fail)"
    return f"NOT PNG ({len(data)}B): {data[:120]!r}"


for key, (base, _) in CANDIDATES.items():
    print(f"\n=== {key}: {base[:70]}")
    res, err = caps(base)
    if err:
        print("  ", err)
        continue
    layers, has3857 = res
    print(f"  layers({len(layers)}): {layers[:8]}")
    print(f"  EPSG:3857: {has3857}")
    layer = pick_layer(layers)
    print(f"  chosen: {layer}")
    if layer:
        print("  map:", try_map(base, layer, *SPOTS[key]))
