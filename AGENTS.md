# AGENTS.md — Projektregeln für KI-Agenten und Mitwirkende

Projekt: **Tile-Caching-and-Offline-Server-Tool-BRD**

Diese Datei definiert verbindliche Regeln für alle Änderungen am Projekt.
Sie gilt für menschliche Mitwirkende und KI-Agenten gleichermaßen.

---

## 1. Versionierung (verbindlich)

- Die Version steht in der Datei **`VERSION`** (Format: `X.Y.Z`, Semantic Versioning).
- **Jede inhaltliche Änderung am Projekt erfordert eine Versionserhöhung:**
  - **MAJOR** (`X.0.0`): Breaking Changes (inkompatible Config-/API-Änderungen).
  - **MINOR** (`x.Y.0`): Neue Features, neue Layer, neue Endpunkte — abwärtskompatibel.
  - **PATCH** (`x.y.Z`): Bugfixes, Doku-Korrekturen, kleine Verbesserungen ohne Feature-Änderung.
- Reine Doku-Korrekturen (Tippfehler in README) dürfen ohne Bump committet werden;
  alles andere zählt als Versionsänderung.
- `serve.py` liest die Version aus `VERSION` und gibt sie über `/version` aus —
  keine zweite Stelle pflegen, `VERSION` ist die Single Source of Truth.

## 2. Changelog (verbindlich)

- **`CHANGELOG.md`** folgt dem Format *Keep a Changelog* (`## [X.Y.Z] - YYYY-MM-DD`).
- Jede Versionsänderung bekommt einen **ausführlichen** Eintrag mit den Abschnitten
  (nur zutreffende): `Added`, `Changed`, `Fixed`, `Removed`, `Security`.
- Pro Änderung ein Bulletpoint mit konkretem Bezug (Datei/Feature/Endpunkt) —
  nicht nur "Diverse Fixes".
- Der neueste Eintrag steht oben. Keine Version ohne Changelog-Eintrag committen.

## 3. KI-Transparenz (verbindlich)

- KI-generierte Beiträge werden transparent gemacht:
  - In `README.md` steht ein Abschnitt **„KI-Nutzung"** mit Software und Modell.
  - Bei KI-generierten Commits: Co-Authored-By-Trailer im Commit.
  - In `CHANGELOG.md` darf ein Eintrag mit `(KI: <Tool>, Modell: <Modellname>)`
    gekennzeichnet werden, wenn die Version überwiegend KI-generiert ist.
- Die verwendete KI-Software und das Modell sind immer aktuell zu dokumentieren.

## 4. Lizenzliste (verbindlich)

- **`THIRD_PARTY_LICENSES.md`** listet alle verwendeten Komponenten und Datenquellen:
  Software (mit Version, Quelle, Lizenz) **und** Kartendienste (mit Anbieter,
  Endpoint, Lizenz, Namensnennung).
- Wird eine Abhängigkeit oder Datenquelle hinzugefügt/entfernt/aktualisiert,
  muss die Lizenzliste in derselben Änderung mitgepflegt werden.
- Das Projekt selbst steht unter **MIT** (`LICENSE`).

## 5. Sensible Daten & Git-Hygiene (verbindlich)

- **Niemals committen:** `config.json` (lokale Konfiguration), `.env*`,
  `tiles/` (Kachel-Cache), `*.log`, `log.txt`, `server.log`, `__pycache__/`.
- Neue Konfigurationsoptionen werden in **`config.example.json`** dokumentiert;
  `config.json` bleibt lokal. `serve.py` fällt automatisch auf die Example-Config
  bzw. eingebaute Defaults zurück.
- Vor jedem Commit prüfen: `git status` — keine Tiles, keine Logs, keine Secrets.

## 6. Abhängigkeiten

- Runtime: Python ≥ 3.10, **nur Standardbibliothek** — kein pip nötig.
- `lib/leaflet.js` + `lib/leaflet.css` (Leaflet 1.9.4) sind vendored und werden
  committet. Bei Update: Version in `THIRD_PARTY_LICENSES.md` anpassen.
- `install.ps1` / `install.sh` laden fehlende Abhängigkeiten (Leaflet) nach —
  bei neuen Abhängigkeiten beide Skripte mitpflegen.

## 7. Build & Release (CI/CD)

- `.github/workflows/release.yml` baut bei jeder `VERSION`-Änderung auf `main`:
  ZIP-Paket → GitHub Release `vX.Y.Z` mit dem Changelog-Abschnitt der Version
  als Release Notes → anschließend werden alte Release-Assets aufgeräumt
  (siehe `KEEP_RELEASES` im Workflow).
- Commits ohne `VERSION`-Änderung lösen kein Release aus.
- Lokales Bauen geht auch via `python build.py` (erzeugt `dist/`).

## 8. Code-Konventionen

- Sprache: Code-Kommentare und UI-Texte auf Deutsch, Dateinamen/Keys Englisch-kompatibel.
- Kompakter, stdlib-naher Python-Stil; kein Framework, keine Build-Tools im
  Frontend — `index.html` ist eine einzelne Datei mit vendored Leaflet.
- Neue Layer: in `config.example.json` (Layer-Definition mit `type`, `base`/`url`,
  `layer`, `max_zoom`, `bbox`) **und** in `index.html` in `LAYER_DEFS` eintragen.
- Tile-Pfad-Konvention: `tiles/{layer_id}/{z}/{x}/{y}.png` (XYZ-Schema, PNG).

## 9. Tests / Verifikation

- Vor jedem Commit mindestens: `python -c "import serve"` (Syntax-/Import-Check)
  und ein manueller Abruf von `http://localhost:8080/version`.
- Für Layer-Änderungen: eine Testkachel je neuem Layer abrufen
  (`/tiles/<layer>/<z>/<x>/<y>.png`) und HTTP 200 + PNG prüfen.
