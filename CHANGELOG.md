# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
Versionierung: [Semantic Versioning](https://semver.org/lang/de/).

## [1.8.0] - 2026-10-08

Versions-Badge mit GitHub-Link und serverseitigem Update-Check;
Download-Button zurück in die Sidebar. (KI: Devin, Modell: SWE-2 High)

### Added

- **Update-Check über `/version`:** Der Server fragt einmal pro Stunde
  (gecacht, asynchron, offline-fehlertolerant) das neueste GitHub-Release
  ab und liefert `latest`/`latest_url`/`repo_url` aus — der Browser muss
  keine externe Anfrage machen (keine Konsolen-Fehler offline).
- **Versions-Badge verlinkt** auf das GitHub-Repo; bei neuerer Release
  erscheint „· Update vX.Y.Z" (orange, verlinkt), bei aktueller Version
  „· aktuell" (grün).

### Changed

- **Download-Button zurück in die Sidebar:** Die Karten-Overlay-
  Steuerung wurde durch einen Sidebar-Button (`#dl-toggle-btn`,
  Stil wie die Sektions-Header) ersetzt. Das Download-Panel öffnet
  weiterhin als Overlay auf der Karte (rechts der Sidebar) und deckt den
  Button damit nicht mehr ab.

### Tests

- `test_39_download_toggle_button` überarbeitet: Button liegt in der
  Sidebar (x<330), Panel öffnet auf der Karte (x≥330) ohne Überlappung.
- `test_38_version_badge` erweitert um Link-Prüfung (Ziel = Repo-URL).
- Neue Klasse `TestUpdateCheck` (3 Tests): Update-verfügbar-Hinweis mit
  Link, „aktuell" bei gleicher Version, stiller Fehlschlag ohne
  Release-Info — jeweils über gepatchten `serve.LATEST_RELEASE`-Cache.
- `test_version`/`test_version_latest_cached`: `/version` enthält die
  neuen Update-Check-Felder und spielt den Cache aus.

## [1.7.0] - 2026-10-08

Download-Panel aus der Sidebar gelöst und als schaltbares Overlay direkt
auf der Karte — deutlich mehr Platz im linken Bereich.
(KI: Devin, Modell: SWE-2 High)

### Changed

- **Download-Panel ist jetzt ein Map-Overlay:** Neuer Leaflet-Control-
  Button „Download" oben links auf der Karte (unter dem Zoom-Control)
  blendet das Panel ein/aus — unabhängig vom Sidebar-Zustand. Die Sidebar
  enthält nur noch Cache-Übersicht, Kartenstatus, Punkte und Statistik.
- Der Button bekommt einen aktiven Zustand (`.active`) solange das Panel
  offen ist.

### Tests

- `test_39_download_toggle_button`: Button existiert, Panel startet
  versteckt, wird per Klick sichtbar/unsichtbar, enthält alle
  Layer-Checkboxen.

## [1.6.0] - 2026-10-08

UI-Anpassung: Landesgrenzen sind jetzt standardmäßig immer sichtbar, und
die Server-Version wird prominent in der Sidebar angezeigt.
(KI: Devin, Modell: SWE-2 High)

### Changed

- **Bundesländer-/Staatsgrenzen immer eingeblendet:** Die Grenzen (Länder
  rot, Staatsgrenze blau, `borderPane` zIndex 700) werden beim Start
  automatisch geladen — der „Grenzen einblenden"-Schalter entfällt.
- **Versions-Badge oben links:** `#version-badge` zeigt „Tile-Server
  vX.Y.Z" (injizierte Server-Version, `TILE_V`) als Kopfzeile der
  linken Sidebar — immer sichtbar ohne Scrollen.

### Tests

- `test_32_borders_always_on`: verifiziert, dass die Checkbox entfernt
  ist und die Grenz-Pfade permanent vorhanden sind.
- `TestVersionBadge.test_38_version_badge`: Badge-Text enthält die
  Server-Version und liegt in der linken Sidebar ganz oben.

## [1.5.0] - 2026-10-08

Grobe Weltgrundkarte als Offline-Basiskarte: Länder-Umrisse und
Ländernamen werden als Vektor-Layer unter allen Kachel-Layern
eingeblendet — kein weißer Hintergrund mehr beim Herauszoomen oder
außerhalb der Landes-Abdeckung. (KI: Devin, Modell: SWE-2 High)

### Added

- **`data/world_countries.geo.json`** (im Repo, ~169 KiB): 180 Länder-
  Polygone auf Natural-Earth-110m-Basis (Public Domain), auf das
  `name`-Attribut und 2 Nachkommastellen reduziert.
- **`worldPane`** (zIndex 60, unter dem Leaflet-TilePane 200): helle
  Landflächen (#ece7d8), dezente Grenzen, Ozean-Hintergrund (#b8cfe0).
- **Ländernamen-Labels** (`.wlbl`): permanente Tooltips am
  Polygon-Schwerpunkt, nur sichtbar auf Zoomstufen < 8 (dort, wo keine
  Landes-Kacheln existieren).
- Checkbox „Weltgrundkarte (Länder & Namen)" im Kartenstatus-Panel
  (standardmäßig an).
- Karte ist jetzt bis Zoom 4 herauszoombar (`minZoom` 4); Kachel-Layer
  behalten `minZoom` 8, sodass unter z8 gar keine Tile-Requests entstehen
  und die Weltgrundkarte durchscheint.

### Tests

- `TestWorldBasemap`: Welt-Polygone im worldPane (≥150, zIndex < 200),
  Ländernamen bei z4 (>100 Labels, u. a. „Germany"), Ozean-Farbe,
  Toggle-Funktion.

## [1.4.0] - 2026-10-08

Vollständige Deutschland-Abdeckung: alle 16 Bundesländer liegen jetzt als
parallele Orthophoto-Layer vor, jeweils an der echten Landesgrenze
maskiert. (KI: Devin, Modell: SWE-2 High)

### Added

- **12 neue Open-Data-DOP-Layer** (alle per GetCapabilities + GetMap
  verifiziert, EPSG:3857, PNG):
  - `bw_dop` — ATKIS DOP20 RGB (LGL-BW, `IMAGES_DOP_20_RGB`)
  - `by_dop` — DOP20 Farbe (Bayer. Vermessungsverwaltung, `by_dop20c`)
  - `bb_dop` — DOP20c Brandenburg+Berlin, gekachelter MapProxy
    (`bebb_dop20c`)
  - `be_dop` — DOP20RGBI 2025 Berlin (`dop_2025`, neue GDI-Berlin-
    Plattform; alter FIS-Broker-Endpunkt abgeschaltet)
  - `hb_dop` — DOP10 2025 Bremen + Bremerhaven als kombinierter
    `LAYERS=dop10_2025_HB,dop10_2025_BHV`-Aufruf
  - `he_dop` — DOP rgb Hessen (`he_dop_rgb`, direkter lika-services-
    Endpunkt statt Mapbender-Proxy)
  - `nw_dop` — DOP NRW (`nw_dop_rgb`, dl-de/zero-2-0)
  - `rp_dop` — DOP20 Rheinland-Pfalz (`rp_dop20`)
  - `sl_dop` — DOP20 Saarland 2025 (`sl_dop20_rgb`, freewms-Endpunkt)
  - `sn_dop` — DOP-RGB Sachsen (`sn_dop_020`)
  - `st_dop` — ATKIS DOP20 Sachsen-Anhalt (`lsa_lvermgeo_dop20_2`)
  - `th_dop` — DOP20 Thüringen (`th_dop`)
- **`verify_tls`-Layer-Option**: `false` deaktiviert die Zertifikats-
  prüfung für Dienste mit unvollständiger Zertifikatskette
  (`geodienste.sachsen.de`, `www.gds-srv.hessen.de` — beide senden das
  Zwischenzertifikat nicht).
- Alle neuen Layer mit `mask` (harter Schnitt an der Landesgrenze) und
  eigener `bbox` für die frühe 404-Abdeckungsprüfung.
- Frontend: 12 neue Checkboxen mit korrekten Attributionen; Regionen-
  Auswahl im Download-Panel um alle Bundesländer erweitert.
- `default_bbox` / `COVERAGE_BBOX` auf Gesamtdeutschland erweitert
  ([47.2, 5.8]–[55.1, 15.1]).
- 12 neue echte Upstream-Tests (`test_real_*_dop`, je eine Kachel an einem
  Stadtzentrum pro Bundesland).

### Fixed

- Test-Mocks akzeptieren den neuen `context`-Parameter von `urlopen`.

### Changed

- `VERSION` → `1.4.0` (Browser-Cache-Busting via `?v=` greift automatisch).

## [1.3.0] - 2026-10-07

Harte Landesgrenz-Maskierung: Kachelinhalte außerhalb der Grenze des
jeweiligen Bundeslandes werden serverseitig transparent geschnitten —
behebt Wasserzeichen-/Fremdflächen (z. B. MV-DOP außerhalb MVs), die
parallele Layer überdeckten. (KI: Devin, Modell: SWE-2 High)

### Added

- **`mask`-Layer-Option** (config.json / config.example.json): Name des
  Bundeslandes aus `data/bundeslaender.geo.json`. `serve.py` schneidet
  Pixel außerhalb der Landesgrenze per Scanline-Fill (Paritätsregel —
  unterstützt MultiPolygone und Löcher/Enklaven) auf Alpha=0. Aktiv für
  `dtk5`, `dop20` (Schleswig-Holstein), `ni_dop20` (Niedersachsen),
  `hh_dop`, `hh_dop_u` (Hamburg), `mv_dop`, `mv_dtk10`
  (Mecklenburg-Vorpommern).
  - Kachel komplett außerhalb -> `404` (Fallback greift)
  - komplett innerhalb -> unverändert durchgereicht (kein Decode-Overhead)
  - Randkachel -> decodiert, maskiert, als RGBA-PNG neu kodiert und
    maskiert gecacht
- `png_decode()` / `png_encode_rgba()` — wiederverwendbarer
  Stdlib-PNG-Decoder/-Encoder (Unfilter 0-4, Colortypes 0/2/3/4/6).
- Tests: `TestStateMask` (Polygon-Load, Inside/Outside/Edge, Passthrough,
  Ausgabe-PNG-Validität) und Server-Tests für maskierte Randkachel +
  404 für komplett außerhalb liegende Kacheln.

### Changed

- `png_is_empty()` nutzt intern jetzt `png_decode()`.

### Notes

- Maskierte Kacheln werden maskiert im Cache abgelegt — die Einmalkosten
  je Randkachel (~0.2-0.5 s) fallen nur beim ersten Abruf an.
- Einmalig `tiles/` leeren oder Cache-Self-Healing abwarten, falls alte
  unmaskierte Kacheln im lokalen Cache liegen.

## [1.2.2] - 2026-10-07

Bugfix: Der Browser-Cache hielt alte weiße/opake Kacheln
(`Cache-Control: max-age=31536000`), sodass das Self-Healing aus 1.2.1
nicht griff. (KI: Devin, Modell: SWE-2 High)

### Fixed

- **Cache-Busting:** Alle Kachel-URLs im Frontend tragen jetzt
  `?v=<server-version>` — eine neue Version invalidiert automatisch den
  Browser-Cache der Kacheln. `index.html` wird dafür serverseitig mit
  eingesetzter `__TILE_SERVER_VERSION__`-Platzhalter-Version und
  `Cache-Control: no-cache` ausgeliefert (statt statisch).
- `serve.py`: Tile-Routing (`GET`/`HEAD`) toleriert nun Query-Strings
  (`urlparse` statt `self.path`-Match).

### Added

- Tests: Tile-Request mit `?v=`-Query, Version-Injection in index.html.

## [1.2.1] - 2026-10-07

Bugfix: einfarbige Kacheln (opak weiß aus der Zeit vor `TRANSPARENT=true`
bzw. von Diensten, die die Transparenz ignorieren) überdeckten bei
parallelen Layern die darunterliegende Karte. (KI: Devin, Modell: SWE-2 High)

### Fixed

- `serve.py`: `png_is_empty()` erkennt Leerkacheln jetzt durch echtes
  PNG-Dekodieren (Filter 0-4, Colortypes 0/2/3/4/6, Bit-Tiefe 8) und
  Pixelvergleich — bisher nur über die Dateigröße (< 512 B), wodurch
  ~755 B große opak-weiße PNGs durchrutschten und andere Layer weiß
  übermalten. Kacheln > 64 KiB werden ohne Dekodieren als 'echt' gewertet.
- `serve.py` — **Cache-Self-Healing:** einfarbige Kacheln im Cache werden
  beim Abruf automatisch verworfen und vom Quellserver neu geladen
  (behebt Altlasten aus v1.0.x ohne manuelles Löschen von `tiles/`).

### Added

- `tests/pngutil.py` — Stdlib-PNG-Builder für realistische Test-Fixtures
  (einfarbig weiß/transparent/schwarz, gemustert).
- Neue Tests: `png_is_empty` gegen echte einfarbige PNGs (weiß/transparent/
  schwarz) + Varianten (kaputte Daten, >64 KiB); Server-Tests für
  opak-weiße Upstream-Antwort (404, kein Cache) und Cache-Self-Healing
  (verworfen + Neuabruf).

## [1.2.0] - 2026-10-07

Umfassende Testsuite (Unit, HTTP-Integration, Browser) mit Debug-Ausgaben;
Frontend-Fallback mit Request-Deduplikation und Fehler-Cache optimiert.
(KI: Devin, Modell: SWE-2 High)

### Added

- **Testsuite unter `tests/`** — ausführbar über `python tests/run_tests.py`
  (Optionen: `--no-browser`, `--no-online`, `--unit`):
  - `test_unit.py` — Koordinaten-/Kachel-Mathe (`lat_lon_to_tile_xy`,
    `tile_range_for_bbox`, Kachel-BBox), Layer-Abdeckung (`tile_covered`),
    Zoom-Grenzen, Leerkachel-Erkennung (`png_is_empty`).
  - `test_server.py` — HTTP-Integrationstests gegen einen echten Testserver
    (temporärer Cache, zufälliger Port): statische Routen, `/version`,
    `/stats`, `/missing`, `/next-missing`, GeoJSON-Auslieferung, Cache-Hit/
    HEAD-Handling, BBox-/min_zoom-404 ohne Upstream-Abruf, Upstream-Erfolg
    mit Cache-Anlage, Leer-/Ungültig-/Fehler-Antworten; optional echte
    WMS-Abrufe (abschaltbar via `SKIP_ONLINE=1` / `--no-online`).
  - `test_browser.py` — Playwright/Chromium-Tests des Frontends:
    Seitenaufbau, dynamische Layer-UI, Canvas-Kacheln mit Inhalt,
    parallele Layer-Aktivierung, Zoom-Fallback (Eltern- wie
    Kind-Kachel-Pfad inkl. gezeichneter Pixel), Grenzen-Overlay
    (16 Landesgrenzen rot + Staatsgrenze blau, `borderPane` zIndex 700),
    Karten-Interaktion und Statusanzeige; Screenshots nach `tests/out/`.
- **Debug-Ausgaben:** `[net]`-Log aller Tile-Requests mit HTTP-Status,
  `[px]`-Pixelestatistik pro Canvas, `[svg]`-Grenzpfad-Auswertung,
  `[console]`/`[pageerror]`-Erfassung; `run_tests.py` mit Abschnitts-
  Bannern und Laufzeit.
- `requirements-dev.txt` — Entwicklungs-Abhängigkeiten (Playwright),
  getrennt vom runtime-freien Server.
- `serve.py`: neue Config-Option `tiles_dir` (Cache-Verzeichnis
  verschiebbar; Tests nutzen ein temporäres Verzeichnis).
- CI: `release.yml` um `test`-Job erweitert — Unit-, Integrations- und
  Browser-Tests laufen vor jedem Release in GitHub Actions; ein Release
  wird nur bei grünen Tests erstellt.
- `build.py`: `tests/` und `requirements-dev.txt` sind im Release-ZIP
  enthalten (`tests/out/`, `__pycache__` ausgenommen).

### Changed

- `index.html` (`FallbackTileLayer`): Request-Deduplikation über
  `_inflight`-Map (gleiche URL wird nur einmal angefragt) und
  `_missing`-Set (404-URLs werden nicht erneut abgefragt, Reset bei
  `zoomend`) — reduziert die Fallback-Requestflut deutlich
  (gemessen: ~1350 → ~420 Requests).
- `index.html`: Kind-Kachel-Fallback auf Tiefe 2 begrenzt (bisher 3) —
  kleinerer Request-Fächer bei weiterhin ausreichender Abdeckung.

### Fixed

- `serve.py`: Verbindungsabbrüche des Clients (`ConnectionError`, z. B.
  abgebrochene Tile-Requests beim Zoomen) erzeugen keine Traceback-Flut
  mehr im Server-Log.

### Notes

- Erkannte Leaflet-Eigenheit: Der SVG-Renderer clipt Polygone außerhalb
  des sichtbaren Bereichs (`d="M0 0"`) — die Grenzpfade sind daher per
  DOM-Anwesenheit statt Sichtbarkeit zu prüfen.
- Browser-Tests benötigen Netzwerkzugriff auf die WMS-Quelldienste
  (Kind-Kachel-Fallback lädt echte Daten); Unit-/Integrations-Tests
  laufen offline (`--no-online`).

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
