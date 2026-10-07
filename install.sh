#!/usr/bin/env bash
# Install-Skript: prüft Python, lädt fehlende Abhängigkeiten (Leaflet) nach,
# legt config.json aus config.example.json an.
set -euo pipefail
cd "$(dirname "$0")"

LEAFLET_VERSION="1.9.4"
LEAFLET_BASE="https://unpkg.com/leaflet@${LEAFLET_VERSION}/dist"

echo "==> Python prüfen"
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "FEHLER: Python nicht gefunden. Bitte Python >= 3.10 installieren." >&2
    exit 1
fi
$PY -c "import sys; assert sys.version_info >= (3, 10), 'Python >= 3.10 benötigt'"
echo "    $($PY --version) gefunden (keine pip-Pakete nötig)"

echo "==> Leaflet ${LEAFLET_VERSION} prüfen"
mkdir -p lib
for f in leaflet.js leaflet.css; do
    if [ ! -s "lib/$f" ]; then
        echo "    lade lib/$f ..."
        curl -fsSL "${LEAFLET_BASE}/$f" -o "lib/$f"
    else
        echo "    lib/$f vorhanden"
    fi
done

if [ ! -f config.json ]; then
    echo "==> config.json aus config.example.json anlegen"
    cp config.example.json config.json
else
    echo "==> config.json vorhanden, wird nicht überschrieben"
fi

echo
echo "Fertig. Start mit:  $PY serve.py   (http://localhost:8080)"
