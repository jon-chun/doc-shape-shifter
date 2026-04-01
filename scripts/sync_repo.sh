#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="${1:-$HOME/code/doc-shape-shifter}"

if [ ! -d "${ROOT_DIR}/.git" ]; then
  mkdir -p "$(dirname "${ROOT_DIR}")"
  git clone https://github.com/jon-chun/doc-shape-shifter.git "${ROOT_DIR}"
  echo "Cloned into ${ROOT_DIR}"
  exit 0
fi

cd "${ROOT_DIR}"

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree is not clean."
  echo "Commit or stash your changes before syncing."
  git status --short
  exit 1
fi

git fetch origin
git switch main
git pull --ff-only origin main

echo "Repo synced at $(git rev-parse --short HEAD)"
