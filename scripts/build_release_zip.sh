#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
ARCHIVE_BASENAME="${1:-doc-shape-shifter-project-$(date +%Y%m%d)}"
if [[ "${ARCHIVE_BASENAME}" == *.zip ]]; then
  ARCHIVE_NAME="${ARCHIVE_BASENAME}"
else
  ARCHIVE_NAME="${ARCHIVE_BASENAME}.zip"
fi
ARCHIVE_PATH="${DIST_DIR}/${ARCHIVE_NAME}"

mkdir -p "${DIST_DIR}"
rm -f "${ARCHIVE_PATH}"

cd "${ROOT_DIR}"

FILES=()
while IFS= read -r -d '' file; do
  FILES+=("${file}")
done < <(git ls-files --cached --others --exclude-standard -z)

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "No files found to archive."
  exit 1
fi

zip -q -r "${ARCHIVE_PATH}" "${FILES[@]}"
echo "${ARCHIVE_PATH}"
