#!/usr/bin/env python3
"""Test-Runner: Unit-, Server-Integrations- und Browser-Tests.

    python tests/run_tests.py                # alles
    python tests/run_tests.py --no-browser   # ohne Browser-Tests
    python tests/run_tests.py --no-online    # ohne echte WMS-Abrufe
    python tests/run_tests.py --unit         # nur Unit-Tests
"""
import argparse
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, TESTS)


def banner(txt):
    print('\n' + '=' * 70 + f'\n  {txt}\n' + '=' * 70)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-browser', action='store_true',
                    help='Browser-Tests (Playwright) überspringen')
    ap.add_argument('--no-online', action='store_true',
                    help='Tests gegen echte WMS-Dienste überspringen')
    ap.add_argument('--unit', action='store_true', help='nur Unit-Tests')
    args = ap.parse_args()

    if args.no_online:
        os.environ['SKIP_ONLINE'] = '1'
        print('[env] SKIP_ONLINE=1 — echte WMS-Abrufe werden übersprungen')

    loader = unittest.TestLoader()
    failures = 0
    t0 = time.time()

    suites = [('Unit-Tests (serve.py-Funktionen)', 'test_unit')]
    if not args.unit:
        suites.append(('HTTP-Integrations-Tests (Server)', 'test_server'))
        if not args.no_browser:
            suites.append(('Browser-Tests (Playwright/Chromium)', 'test_browser'))

    for title, mod in suites:
        banner(title)
        try:
            suite = loader.loadTestsFromName(mod)
        except Exception as e:
            print(f'[FATAL] Modul {mod} nicht ladbar: {e}')
            failures += 1
            continue
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        failures += len(result.failures) + len(result.errors)

    banner('Ergebnis')
    if failures:
        print(f'FEHLER: {failures} fehlgeschlagene Tests '
              f'(nach {time.time() - t0:.1f}s)')
        sys.exit(1)
    print(f'Alle Tests bestanden ({time.time() - t0:.1f}s)')


if __name__ == '__main__':
    main()
