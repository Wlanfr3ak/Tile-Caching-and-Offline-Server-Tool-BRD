#!/usr/bin/env python3
"""Baut das Release-ZIP unter dist/ — wird lokal und vom CI-Workflow genutzt."""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

PACKAGE_FILES = [
    'serve.py',
    'index.html',
    'config.example.json',
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'AGENTS.md',
    'THIRD_PARTY_LICENSES.md',
    'VERSION',
    'install.sh',
    'install.ps1',
    'build.py',
    'requirements-dev.txt',
]
PACKAGE_DIRS = ['lib', 'data', 'tests']
# Innerhalb der PACKAGE_DIRS nicht mit ins Paket:
EXCLUDE_DIRS = {'out', '__pycache__'}
NAME = 'Tile-Caching-and-Offline-Server-Tool-BRD'


def main():
    with open(os.path.join(ROOT, 'VERSION'), encoding='utf-8') as f:
        version = f.read().strip()

    dist = os.path.join(ROOT, 'dist')
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, f'{NAME}-v{version}.zip')

    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in PACKAGE_FILES:
            path = os.path.join(ROOT, rel)
            if os.path.isfile(path):
                z.write(path, rel)
            else:
                print(f'WARN: {rel} fehlt', file=sys.stderr)
        for d in PACKAGE_DIRS:
            for dirpath, dirs, files in os.walk(os.path.join(ROOT, d)):
                dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
                for fn in files:
                    if fn.endswith('.pyc'):
                        continue
                    full = os.path.join(dirpath, fn)
                    z.write(full, os.path.relpath(full, ROOT))

    size = os.path.getsize(out)
    print(f'{out}  ({size / 1024:.0f} KiB)')


if __name__ == '__main__':
    main()
