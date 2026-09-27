#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11 or newer is required." >&2
  exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else "Python 3.11+ required")'

if command -v uv >/dev/null 2>&1; then
  uv_command="$(command -v uv)"
else
  python3 -m venv .bootstrap
  .bootstrap/bin/python -m pip install --disable-pip-version-check 'uv==0.6.3'
  uv_command="$project_dir/.bootstrap/bin/uv"
fi

"$uv_command" sync --frozen --no-dev
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "Python package installed. Install FFmpeg to generate audio:" >&2
  echo "  macOS: brew install ffmpeg" >&2
  echo "  Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y ffmpeg" >&2
  exit 2
fi
"$project_dir/.venv/bin/python" -m article_audio doctor
