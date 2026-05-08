#!/usr/bin/env python3
"""Regenera reports/report-navigator.html após generateAllureReport.sh (watcher / CLI)."""
import os
import sys

ROOT = os.environ.get('ROOT', '/app')
sys.path.insert(0, os.path.join(ROOT, 'allure-docker-api'))

from app import app, write_report_navigator_scaffold  # pylint: disable=wrong-import-position

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    with app.app_context():
        write_report_navigator_scaffold(sys.argv[1])
