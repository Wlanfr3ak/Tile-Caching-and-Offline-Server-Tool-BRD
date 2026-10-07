# Lizenzliste — THIRD_PARTY_LICENSES.md

Liste aller verwendeten Software-Komponenten und Datenquellen mit Quelle und
Lizenz. Pflege gemäß `AGENTS.md` §4: jede neue/geänderte/entfernte
Abhängigkeit oder Datenquelle wird hier in derselben Änderung aktualisiert.

## Software / Libraries

| Komponente        | Version | Quelle                                          | Lizenz                                      |
|-------------------|---------|-------------------------------------------------|---------------------------------------------|
| Python            | ≥ 3.10  | https://www.python.org                          | PSF License                                 |
| Leaflet           | 1.9.4   | https://leafletjs.com (`lib/leaflet.js`, vendored) | BSD-2-Clause                              |
| deutschlandGeoJSON (Bundesländer-/Staatsgrenzen) | 3_mittel | https://github.com/isellsoap/deutschlandGeoJSON (`data/`, vendored) | Unlicense (Public Domain); Basis: BKG VG250, dl-de/by-2-0 |
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
| `osm`      | OpenStreetMap Tile Server                           | https://tile.openstreetmap.org                                           | ODbL + Tile Usage Policy | © OpenStreetMap contributors             |

### Lizenz-Referenzen

- **dl-de/by-2-0** — Datenlizenz Deutschland – Namensnennung – Version 2.0:
  https://www.govdata.de/dl-de/by-2-0
- **ODbL** — Open Database License: https://opendatacommons.org/licenses/odbl/
- **OSM Tile Usage Policy:** https://operations.osmfoundation.org/policies/tiles/
  (kein massenhaftes Scraping; der Server cached nur angefragte Kacheln)
- **BSD-2-Clause** (Leaflet): https://github.com/Leaflet/Leaflet/blob/main/LICENSE
- **PSF** (Python): https://docs.python.org/3/license.html
