# Lizenzliste — THIRD_PARTY_LICENSES.md

Liste aller verwendeten Software-Komponenten und Datenquellen mit Quelle und
Lizenz. Pflege gemäß `AGENTS.md` §4: jede neue/geänderte/entfernte
Abhängigkeit oder Datenquelle wird hier in derselben Änderung aktualisiert.

## Software / Libraries

| Komponente        | Version | Quelle                                          | Lizenz                                      |
|-------------------|---------|-------------------------------------------------|---------------------------------------------|
| Python            | ≥ 3.10  | https://www.python.org                          | PSF License                                 |
| Leaflet           | 1.9.4   | https://leafletjs.com (`lib/leaflet.js`, vendored) | BSD-2-Clause                              |
| deutschlandGeoJSON (deutsche Staatsgrenze, `data/deutschland.geo.json`) | 3_mittel | https://github.com/isellsoap/deutschlandGeoJSON (`data/`, vendored) | Unlicense (Public Domain); Basis: BKG VG250, dl-de/by-2-0 |
| OpenStreetMap (Bundesländergrenzen, `data/bundeslaender.geo.json` — admin_level=4-Relationen via Nominatim, Douglas-Peucker-vereinfacht) | 2026-10 | https://www.openstreetmap.org | ODbL; © OpenStreetMap contributors |
| world.geo.json / Natural Earth 110m (Welt-Ländergrenzen) | — | https://github.com/johan/world.geo.json (`data/world_countries.geo.json`, vendored, auf `name`+2-Nachkommastellen reduziert) | Public Domain (Natural Earth) |
| GitHub Actions    | —       | `actions/checkout`, `softprops/action-gh-release` | MIT / siehe jeweiliges Action-Repo         |

### Entwicklungs-Abhängigkeiten (nur Tests, `requirements-dev.txt`)

| Komponente        | Version | Quelle                                          | Lizenz                                      |
|-------------------|---------|-------------------------------------------------|---------------------------------------------|
| Playwright        | 1.63.0  | https://playwright.dev (pip `playwright`)       | Apache-2.0                                  |
| pyee              | ≥ 13    | https://pypi.org/project/pyee (Playwright-Dep.) | MIT                                         |
| greenlet          | ≥ 3.5   | https://pypi.org/project/greenlet (Playwright-Dep.) | MIT                                     |

Keine weiteren Runtime-Abhängigkeiten — der Server nutzt ausschließlich die
Python-Standardbibliothek.

## Datenquellen / Kartendienste

Alle Dienste sind offizielle Open-Data-/Geobasisdaten-Dienste der Länder.
Die gecachten Kacheln unterliegen den Nutzungsbedingungen der Quelle —
Attribution im Viewer ist voreingestellt.

| Layer      | Dienst / Anbieter                                   | Endpoint                                                                 | Lizenz              | Namensnennung                                |
|------------|-----------------------------------------------------|--------------------------------------------------------------------------|---------------------|-----------------------------------------------|
| `dtk5`     | WMS SH DTK5 — LVermGeo Schleswig-Holstein           | https://service.gdi-sh.de/WMS_SH_DTK5_OpenGBD                            | dl-de/by-2-0 (OpenGBD) | GeoBasis-DE/LVermGeo SH                    |
| `dop20`    | WMS SH DOP20 — LVermGeo Schleswig-Holstein          | https://dienste.gdi-sh.de/WMS_SH_DOP20col_OpenGBD                        | dl-de/by-2-0 (OpenGBD) | GeoBasis-DE/LVermGeo SH                    |
| `ni_dop20` | WMS NI DOP20 — LGLN Niedersachsen (OpenData)        | https://opendata.lgln.niedersachsen.de/doorman/noauth/dop_wms            | dl-de/by-2-0        | LGLN, https://www.lgln.niedersachsen.de       |
| `hh_dop`   | WMS DOP Zeitreihe belaubt — FHH, LGV                | https://geodienste.hamburg.de/wms_dop_zeitreihe_belaubt                  | dl-de/by-2-0        | Freie und Hansestadt Hamburg, LGV             |
| `hh_dop_u` | WMS DOP Zeitreihe unbelaubt — FHH, LGV              | https://geodienste.hamburg.de/wms_dop_zeitreihe_unbelaubt                | dl-de/by-2-0        | Freie und Hansestadt Hamburg, LGV             |
| `mv_dop`   | WMS Digitale Orthophotos MV — LAiV M-V              | https://www.geodaten-mv.de/dienste/adv_dop                               | dl-de/by-2-0        | GeoBasis-DE/LVermGeo M-V                      |
| `mv_dtk10` | WMS DTK10 MV — LAiV M-V                             | https://www.geodaten-mv.de/dienste/adv_dtk10                             | dl-de/by-2-0        | GeoBasis-DE/LVermGeo M-V                      |
| `bw_dop`   | WMS ATKIS DOP20 RGB — LGL Baden-Württemberg          | https://owsproxy.lgl-bw.de/owsproxy/ows/WMS_LGL-BW_ATKIS_DOP_20_C        | dl-de/by-2-0        | LGL, https://www.lgl-bw.de                    |
| `by_dop`   | WMS DOP20 — Bayerische Vermessungsverwaltung         | https://geoservices.bayern.de/od/wms/dop/v1/dop20                        | CC BY 4.0           | Bayerische Vermessungsverwaltung – geodaten.bayern.de |
| `bb_dop`   | WMS DOP20c — GeoBasis-DE/LGB Brandenburg (BB+BE)     | https://isk.geobasis-bb.de/mapproxy/dop20c/service/wms                   | dl-de/by-2-0        | GeoBasis-DE/LGB, dl-de/by-2-0                 |
| `be_dop`   | WMS DOP20RGBI 2025 — SenSBW Berlin                   | https://gdi.berlin.de/services/wms/dop_2025_fruehjahr                    | dl-de/by-2-0        | Senatsverwaltung Berlin                       |
| `hb_dop`   | WMS Orthophotos Land Bremen — FHB                    | https://geodienste.bremen.de/wms_dop_lb                                  | dl-de/by-2-0        | Freie Hansestadt Bremen                       |
| `he_dop`   | WMS DOP — HVBG Hessen                                | https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-images.ows  | dl-de/by-2-0        | Hessische Verwaltung für Bodenmanagement und Geoinformation |
| `nw_dop`   | WMS NW Digitale Orthophotos — Geobasis NRW           | https://www.wms.nrw.de/geobasis/wms_nw_dop                               | dl-de/zero-2-0      | Geobasis NRW                                  |
| `rp_dop`   | WMS RP DOP20 — LVermGeo Rheinland-Pfalz              | https://geo4.service24.rlp.de/wms/rp_dop20.fcgi                          | dl-de/by-2-0        | GeoBasis-DE/LVermGeoRP                        |
| `sl_dop`   | WMS SL DOP20 — LVGL Saarland                         | https://geoportal.saarland.de/freewms/dop2025                            | dl-de/by-2-0        | LVGL Saarland                                 |
| `sn_dop`   | WMS SN DOP-RGB — GeoSN Sachsen                       | https://geodienste.sachsen.de/wms_geosn_dop-rgb/guest                    | dl-de/by-2-0        | GeoSN Sachsen                                 |
| `st_dop`   | WMS ST DOP20 OpenData — LVermGeo Sachsen-Anhalt      | https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest | dl-de/by-2-0 | LVermGeo Sachsen-Anhalt          |
| `th_dop`   | WMS DOP20 — GDI-Th / TLVermGeo Thüringen             | https://www.geoproxy.geoportal-th.de/geoproxy/services/DOP20             | dl-de/by-2-0        | © GDI-Th                                      |
| `osm`      | OpenStreetMap Tile Server                           | https://tile.openstreetmap.org                                           | ODbL + Tile Usage Policy | © OpenStreetMap contributors             |

### Lizenz-Referenzen

- **dl-de/by-2-0** — Datenlizenz Deutschland – Namensnennung – Version 2.0:
  https://www.govdata.de/dl-de/by-2-0
- **dl-de/zero-2-0** — Datenlizenz Deutschland – Zero – Version 2.0:
  https://www.govdata.de/dl-de/zero-2-0
- **CC BY 4.0** (Bayern): https://creativecommons.org/licenses/by/4.0/deed.de
- **Hinweis TLS:** `sn_dop` (geodienste.sachsen.de) und `he_dop`
  (gds-srv.hessen.de) senden unvollständige Zertifikatsketten; für diese Layer
  ist `verify_tls: false` konfiguriert (siehe `config.example.json`).
- **ODbL** — Open Database License: https://opendatacommons.org/licenses/odbl/
- **OSM Tile Usage Policy:** https://operations.osmfoundation.org/policies/tiles/
  (kein massenhaftes Scraping; der Server cached nur angefragte Kacheln)
- **BSD-2-Clause** (Leaflet): https://github.com/Leaflet/Leaflet/blob/main/LICENSE
- **PSF** (Python): https://docs.python.org/3/license.html
