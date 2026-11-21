#!/usr/bin/env bash
# Install the photo-to-3d skill for Claude Code: link the skill into the skills folder and make the
# Python environment that Blender borrows numpy and Pillow from (it must match Blender's Python version).
#   PHOTO3D_HOME       where models and the environment live (default ~/photo-to-3d)
#   CLAUDE_SKILLS_DIR  Claude Code's skills folder (default ~/.claude/skills)
set -euo pipefail
repo="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
export PHOTO3D_HOME="${PHOTO3D_HOME:-$HOME/photo-to-3d}"
skills="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

command -v blender >/dev/null || { echo "Blender is not on PATH: install Blender first" >&2; exit 1; }
ver=$(blender -b --factory-startup --python-expr "import sys; print('PYVER %d.%d' % sys.version_info[:2])" 2>&1 \
      | awk '/^PYVER/ {print $2}' || true)
[ -n "$ver" ] || { echo "could not read Blender's Python version: does 'blender -b' run?" >&2; exit 1; }
py=$(command -v "python$ver" || true)
[ -n "$py" ] || { echo "Blender runs Python $ver: install python$ver (with venv) so Blender can borrow numpy and Pillow" >&2; exit 1; }

mkdir -p "$PHOTO3D_HOME/models" "$skills"
venv="$PHOTO3D_HOME/.venv"
# (re)make the environment when it is missing, half-made (no pip) or for another Python version
if [ ! -x "$venv/bin/pip" ] || [ ! -d "$venv/lib/python$ver" ]; then
  "$py" -m venv --clear "$venv" || { echo "making $venv failed: install the venv module for python$ver" >&2; exit 1; }
fi
"$venv/bin/pip" install -q -r "$repo/requirements.txt"

link="$skills/photo-to-3d"
if [ -e "$link" ] && [ ! -L "$link" ]; then
  echo "$link already exists and is not a link: move it away, then run this again" >&2; exit 1
fi
ln -sfn "$repo/skill/photo-to-3d" "$link"
echo "skill linked: $link -> $repo/skill/photo-to-3d"
"$link/scripts/model3d" check
if [ "$PHOTO3D_HOME" != "$HOME/photo-to-3d" ]; then
  echo "note: add  export PHOTO3D_HOME=\"$PHOTO3D_HOME\"  to your shell profile so model3d and Claude Code find it"
fi
