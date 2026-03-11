#!/bin/bash
cd "$(dirname "$0")"
[ -z "$VIRTUAL_ENV" ] && [ -f "venv/bin/activate" ] && source venv/bin/activate
python basla.py
