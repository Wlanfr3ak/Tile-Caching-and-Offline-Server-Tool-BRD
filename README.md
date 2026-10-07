# Tile-Caching-and-Offline-Server-Tool-BRD

Lokaler Tile-Caching- und Offline-Kartenserver für offene Geodatendienste
(WMS/XYZ) der Bundesrepublik Deutschland — mit Leaflet-Weboberfläche,
Cache-Statistiken und Kachel-Download-Tools.

Der Server ruft fehlende Kacheln von den offiziellen Open-Data-Diensten der
Bundesländer ab und speichert sie lokal unter `tiles/{layer}/{z}/{x}/{y}.png`
(standard XYZ-Schema, PNG). Der Cache ist damit offline nutzbar und kann auch
von anderen Programmen (GIS, MBTiles-Tools, OSM-Viewer) weiterverwendet werden.

## Features

- **Offline-Karten-Cache:** einmal geladene Kacheln liegen persistent lokal vor
- **Leaflet-Viewer** (`index.html`) mit Layer-Auswahl, Entfernungsmessung,
  Koordinaten-Punkten (Lat/Lon, DMS, DDM, EPSG:3857, GeoJSON)
- **Zoom-Fallback:** Fehlt eine Kachel in der angefragten Zoomstufe, wird
  automatisch die nächste vorhandene Stufe hoch- bzw. herunterskaliert
  dargestellt (Qualität sinkt entsprechend, Anzeige bleibt aber erhalten)
- **Parallele Landes-Layer:** mehrere Layer gleichzeitig einblendbar —
  Gebiete ohne Abdeckung sind transparent, nicht weiß (WMS `TRANSPARENT=true`)
- **Grenzen-Overlay:** Bundesländergrenzen rot + Staatsgrenze blau, per
  Checkbox über allen Layern einblendbar (lokale Geometrien in `data/`)
- **Batch-Download:** Kacheln für Region oder Kartenausschnitt vollständig laden,
  inkl. Auto-Erkundungs- und Heißluftballon-Modus
- **Cache-Statistiken:** pro Layer und Zoomstufe (`/stats`)
- **REST-Endpunkte:** `/tiles/{layer}/{z}/{x}/{y}.png`, `/stats`, `/missing`,
  `/next-missing`, `/version`
- **Konfigurierbar** über `config.json` (siehe `config.example.json`) —
  Layer, Port, BBoxen, User-Agent ohne Codeänderung anpassbar
- **Keine externen Python-Abhängigkeiten** — nur Standardbibliothek

## Enthaltene Kartenlayer (Open Data)

| Layer-ID    | Inhalt                                    | Quelle                          |
|-------------|-------------------------------------------|---------------------------------|
| `dtk5`      | DTK5 Topographie Schleswig-Holstein       | LVermGeo SH                     |
| `dop20`     | DOP20 Orthophotos Schleswig-Holstein      | LVermGeo SH                     |
| `ni_dop20`  | DOP20 Orthophotos Niedersachsen           | LGLN Niedersachsen              |
| `hh_dop`    | DOP-Zeitreihe belaubt Hamburg             | FHH / LGV                       |
| `hh_dop_u`  | DOP-Zeitreihe unbelaubt Hamburg           | FHH / LGV                       |
| `mv_dop`    | DOP Orthophotos Mecklenburg-Vorpommern    | LAiV M-V                        |
| `mv_dtk10`  | DTK10 Topographie Mecklenburg-Vorpommern  | LAiV M-V                        |
| `osm`       | OpenStreetMap                             | OSM / tile.openstreetmap.org    |

Details und Lizenzen siehe [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Quickstart

```bash
# Optional: Abhängigkeiten prüfen/nachladen (Leaflet), config.json anlegen
./install.sh          # Linux/macOS
.\install.ps1         # Windows PowerShell

python serve.py
# Browser: http://localhost:8080
```

Voraussetzung: **Python ≥ 3.10**. Es werden keine pip-Pakete benötigt.

## Konfiguration

`config.json` anlegen (oder `config.example.json` kopieren) — wird **nicht**
committet und ist der Ort für lokale Anpassungen und ggf. sensible Endpunkte.
Fehlt die Datei, nutzt der Server die eingebauten Defaults bzw.
`config.example.json`.

```json
{
  "port": 8080,
  "min_zoom": 8,
  "layers": { "<id>": { "type": "wms|xyz", "base|url": "...", "layer": "...",
                        "max_zoom": 19, "bbox": [s, w, n, e] } }
}
```

## Projektstruktur

```
serve.py               # Tile-Server (Python stdlib)
index.html             # Leaflet-Frontend
config.example.json    # Vorlage-Konfiguration
config.json            # lokale Config (gitignored)
lib/                   # vendored Leaflet 1.9.4
data/                  # Bundesländer-/Staatsgrenzen (GeoJSON, vendored)
tiles/                 # Kachel-Cache (gitignored)
install.sh/.ps1        # Abhängigkeiten nachladen
build.py               # Release-Paket bauen (dist/)
VERSION / CHANGELOG.md # Versionierung
```

## Versionierung & Releases

Jede Versionsänderung wird in [`CHANGELOG.md`](CHANGELOG.md) ausführlich
dokumentiert. Bei einem Push mit geänderter `VERSION` auf `main` erstellt
GitHub Actions automatisch ein Release `vX.Y.Z` mit ZIP-Build und den
Changelog-Notes dieser Version; alte Release-Assets werden aufgeräumt.
Regeln dazu: [`AGENTS.md`](AGENTS.md).

## KI-Nutzung

Dieses Projekt wird (teil-)weise mit KI-Unterstützung entwickelt.
Transparenzhinweis gemäß `AGENTS.md`:

- **Tool:** Devin (Cognition), interaktiver Coding-Agent
- **Modell:** SWE-2 High
- **Umfang:** Code, Konfiguration, CI/CD, Dokumentation — jeweils im
  `CHANGELOG.md` pro Version gekennzeichnet

## Lizenzen

- **Projekt:** [MIT](LICENSE)
- **Drittkomponenten & Datenquellen:** [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)
- **Wichtig:** Die gecachten Kacheln unterliegen den Nutzungsbedingungen der
  jeweiligen Datenquellen (siehe Lizenzliste). Für OSM-Kacheln gilt die
  [OSM Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/).
