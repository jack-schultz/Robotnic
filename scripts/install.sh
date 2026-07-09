#!/usr/bin/env bash
set -euo pipefail

pip install -r requirements.txt
pip install -r requirements-topgg.txt --no-deps
