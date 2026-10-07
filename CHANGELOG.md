# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
Versionierung: [Semantic Versioning](https://semver.org/lang/de/).

## [1.1.0] - 2026-10-07

Zoom-Fallback für fehlende Kacheln, parallele Landes-Layer und
Grenzen-Overlay. (KI: Devin, Modell: SWE-2 High)

### Added

- **Zoom-Fallback (`FallbackTileLayer`):** Fehlt eine Kachel in der
  angefragten Zoomstufe (404 oder Leerkachel), lädt das Frontend
  automatisch die nächstgröbere vorhandene Stufe und skaliert sie hoch
  (bis 4 Stufen); liegt auch dort nichts vor, werden die 4 Kind-Kacheln
  der nächstfeineren Stufe herunterskaliert kompositiert (rekursiv bis
  Tiefe 3). Darstellung erfolgt über Canvas-Kacheln.
- **Parallele Landes-Layer:** Die einstufige Basis-Layer-Auswahl wurde
  durch eine Checkbox-Liste ersetzt — mehrere Layer (z. B. Orthophotos
  mehrerer Bundesländer) sind gleichzeitig überlagerbar. Möglich wird das
  durch `TRANSPARENT=true` bei allen WMS-Anfragen: Gebiete außerhalb der
  Datenabdeckung werden transparent statt weiß ausgeliefert.
- **Grenzen-Overlay:** Aktivierbarer Layer, der alle Bundesländergrenzen
  rot und die deutsche Staatsgrenze blau einblendet. Liegt in eigenem
  Pane (`borderPane`, zIndex 700) immer über allen anderen Layern und ist
  nicht klickbar. Geometrien lokal unter `data/` (deutschlandGeoJSON,
  Unlicense / Basis BKG VG250).
- **Server:** `png_is_empty()` — vollständig transparente/leere Antworten
  des Quellservers (< 512 B) werden als „fehlend" behandelt (404, kein
  Cache-Eintrag), sodass das Zoom-Fallback greift.
- **Server:** `tile_covered()` — Kacheln außerhalb der Layer-`bbox` oder
  außerhalb des konfigurierten Zoom-Bereichs werden sofort mit 404
  beantwortet, ohne Upstream-Abruf und ohne Cache-Eintrag.
- **Config:** neue optionale Layer-Optionen `min_zoom` und `transparent`
  (Standard `true`); Schema-Hinweis in `config.example.json`.

### Changed

- `serve.py`: WMS-Anfragen nutzen nun `TRANSPARENT=true` (pro Layer per
  `transparent` steuerbar).
- `mv_dtk10`: `min_zoom` 15 gesetzt (Quelle rendert erst ab ~1:10k-Maßstab);
  darunter greift der Kind-Kachel-Fallback bzw. die Statusanzeige.

### Fixed

- `serve.py`: Meta-Schlüssel in der Layer-Config (`_schema`) werden
  herausgefiltert, sodass sie nicht als Layer interpretiert werden.

## [1.0.0] - 2026-10-07

Erste öffentliche Version — Aufbereitung für GitHub + Erweiterung auf
Niedersachsen, Hamburg und Mecklenburg-Vorpommern.
(KI: Devin, Modell: SWE-2 High)

### Added

- **Neue Open-Data-Layer:**
  - `ni_dop20` — DOP20-Orthophotos Niedersachsen (LGLN OpenData WMS)
  - `hh_dop` — DOP-Zeitreihe belaubt Hamburg (geodienste.hamburg.de)
  - `hh_dop_u` — DOP-Zeitreihe unbelaubt Hamburg (geodienste.hamburg.de)
  - `mv_dop` — DOP-Orthophotos Mecklenburg-Vorpommern (LAiV M-V, `adv_dop`)
  - `mv_dtk10` — DTK10-Topographie Mecklenburg-Vorpommern (`adv_dtk10`)
- **Konfiguration:** `config.json` (lokal, gitignored) mit Fallback auf
  `config.example.json` und eingebaute Defaults — Layer, Port, BBoxen und
  User-Agent sind nun ohne Codeänderung konfigurierbar (`serve.py`,
  `load_config()`).
- **Versionierung:** `VERSION`-Datei als Single Source of Truth; `serve.py`
  stellt die Version über neuen Endpunkt `GET /version` bereit und loggt sie
  beim Start.
- **Frontend:** Regionen-Auswahl erweitert um „Ganz Niedersachsen",
  „Ganz Hamburg", „Ganz Mecklenburg-Vorpommern"; `LAYER_DEFS` als zentrale
  Layer-Definition — Checkboxen, Basis-Layer-Select, Statusanzeige und
  Statistik-Tabelle werden dynamisch daraus aufgebaut.
- **Dokumentation:** `AGENTS.md` (verbindliche Projektregeln: Versionierung,
  Changelog, KI-Transparenz, Lizenzpflege, Git-Hygiene), `README.md`,
  `THIRD_PARTY_LICENSES.md` (Lizenzliste aller Software & Datenquellen),
  `LICENSE` (MIT), `CHANGELOG.md`.
- **Build/CI:** `build.py` erzeugt Release-ZIP unter `dist/`; GitHub Actions
  Workflow `.github/workflows/release.yml` baut bei `VERSION`-Änderung auf
  `main` automatisch ein Release `vX.Y.Z` mit Changelog-Notes und räumt alte
  Releases auf (behält die letzten 5).
- **Setup:** `install.sh` und `install.ps1` prüfen Python und laden fehlende
  Leaflet-Dateien (1.9.4, gepinnt) nach; legen `config.json` aus der
  Example-Datei an.
- **Git-Hygiene:** `.gitignore` für `tiles/`, Logs, `config.json`, `.env`,
  `__pycache__/`, Build-Artefakte.

### Changed

- `serve.py`: Tile-Routing-Regex generalisiert (`[a-z0-9_]+` statt
  festverdrahteter Layer-Liste) — neue Layer funktionieren ohne Codeänderung.
- `serve.py`: `/stats` berechnet die Abdeckung pro Layer anhand dessen
  eigener `bbox` aus der Config statt globaler SH-BBox.
- `index.html`: Karten-`maxBounds` auf gesamte Abdeckung Norddeutschland
  (BRD-Nord) erweitert; Seitentitel aktualisiert.

### Notes

- Der Hamburg-DOP-WMS ist eine Zeitreihe (WMS-Time, Default: aktuellster
  Jahrgang); der Server fragt ohne `TIME`-Parameter an und erhält dadurch
  immer den neuesten Stand.
