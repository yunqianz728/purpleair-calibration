#!/usr/bin/env sh
set -eu

if [ ! -f app.py ]; then
  echo "Run this script from the app directory."
  exit 1
fi

python -m streamlit run app.py
