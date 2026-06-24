#!/usr/bin/env bash
# Run all available validation for the passive cooling blueprint.
# Mirrors the checks performed in CI so they can be run locally.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> yamllint"
yamllint blueprints/ .yamllint

echo "==> Blueprint logic tests"
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo "==> All validation passed"
