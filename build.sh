#!/bin/sh
# Builds one zip per skill into dist/ for upload in claude.ai (Organization settings → Skills).
# evals/ stays out of the packages.
set -eu
cd "$(dirname "$0")"
rm -rf dist && mkdir dist
for dir in skills/*/; do
  name=$(basename "$dir")
  (cd skills && zip -qr "../dist/$name.zip" "$name" -x "$name/evals/*" "*.DS_Store")
  echo "dist/$name.zip"
done
