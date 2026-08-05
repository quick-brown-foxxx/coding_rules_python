#!/usr/bin/env bash

set -euo pipefail

# Bootstrap a new downstream Python project from the coding_rules_python
# templates.
#
# The source can be:
#   - a local checkout path (backward-compatible), e.g. /path/to/coding_rules_python
#   - an upstream URL (git://, git@, https://, ssh://), defaulting to the
#     quick-brown-foxxx/coding_rules_python repo on GitHub
#
# It promotes template files into place, copies shared/, shared_tests/ and
# docs, creates the CLAUDE.md symlink, then runs:
#   uv sync --all-extras --group dev
#   uv run poe lint_full
#   uv run poe test
#
# Usage: %s [SOURCE_REPO] TARGET_REPO
#   SOURCE_REPO: local checkout path or upstream URL (defaults to GitHub)
#   TARGET_REPO : destination directory for the new project
#
# GNU/Linux-first bootstrap helper: `realpath -m` lets us normalize a target
# path that may not exist yet. Broaden this when the bootstrap needs other
# platforms.

DEFAULT_SOURCE="https://github.com/quick-brown-foxxx/coding_rules_python.git"

is_url() {
  case "$1" in
    git@* | git://* | ssh://* | https://* | http://* | file://*) return 0 ;;
    *) return 1 ;;
  esac
}

require_missing_path() {
  local path="$1"
  if [ -e "$path" ] || [ -L "$path" ]; then
    printf 'Target path already exists: %s\n' "$path" >&2
    exit 1
  fi
}

require_source_file() {
  local path="$1"
  if [ ! -f "$path" ]; then
    printf 'Missing required source file: %s\n' "$path" >&2
    exit 1
  fi
}

require_source_dir() {
  local path="$1"
  if [ ! -d "$path" ]; then
    printf 'Missing required source directory: %s\n' "$path" >&2
    exit 1
  fi
}

copy_file() {
  local source_path="$1"
  local target_path="$2"

  require_source_file "$source_path"
  require_missing_path "$target_path"
  mkdir -p "$(dirname "$target_path")"
  cp "$source_path" "$target_path"
}

copy_directory() {
  local source_path="$1"
  local target_path="$2"

  require_source_dir "$source_path"
  require_missing_path "$target_path"
  cp -R "$source_path" "$target_path"
}

usage() {
  printf 'Usage: %s [SOURCE_REPO] TARGET_REPO\n' "$0" >&2
  printf '  SOURCE_REPO: local checkout path or upstream URL (default: %s)\n' "$DEFAULT_SOURCE" >&2
  printf '  TARGET_REPO : destination directory for the new project\n' >&2
  exit 1
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  usage
fi

SOURCE_ARG="$1"
TARGET_ARG="${2:-}"

# One argument means: default source, that argument is the target.
if [ -z "$TARGET_ARG" ]; then
  TARGET_ARG="$SOURCE_ARG"
  SOURCE_ARG="$DEFAULT_SOURCE"
fi

TARGET_ROOT=$(realpath -m "$TARGET_ARG")
require_missing_path "$TARGET_ROOT"
mkdir -p "$TARGET_ROOT"

TMP_SOURCE=""

# Resolve the source: fetch upstream into a temp dir, or use a local checkout.
if is_url "$SOURCE_ARG"; then
  TMP_SOURCE="$(mktemp -d)"
  trap 'rm -rf "$TMP_SOURCE"' EXIT

  printf 'Fetching upstream from %s\n' "$SOURCE_ARG"
  git clone --quiet --depth 1 "$SOURCE_ARG" "$TMP_SOURCE/source"

  SOURCE_ROOT="$TMP_SOURCE/source"
else
  SOURCE_ROOT=$(realpath "$SOURCE_ARG")
fi

copy_directory "$SOURCE_ROOT/shared" "$TARGET_ROOT/shared"
copy_directory "$SOURCE_ROOT/shared_tests" "$TARGET_ROOT/shared_tests"

copy_file "$SOURCE_ROOT/templates/AGENTS.md" "$TARGET_ROOT/AGENTS.md"
copy_file "$SOURCE_ROOT/templates/pyproject.toml" "$TARGET_ROOT/pyproject.toml"
copy_file "$SOURCE_ROOT/templates/pre-commit-config.yaml" "$TARGET_ROOT/.pre-commit-config.yaml"
copy_directory "$SOURCE_ROOT/templates/src" "$TARGET_ROOT/src"
copy_directory "$SOURCE_ROOT/templates/tests" "$TARGET_ROOT/tests"
copy_file "$SOURCE_ROOT/templates/gitignore" "$TARGET_ROOT/.gitignore"
copy_file "$SOURCE_ROOT/templates/vscode_settings.json" "$TARGET_ROOT/.vscode/settings.json"
copy_file "$SOURCE_ROOT/templates/vscode_extensions.json" "$TARGET_ROOT/.vscode/extensions.json"

copy_file "$SOURCE_ROOT/rules/coding_rules.md" "$TARGET_ROOT/docs/coding_rules.md"

require_missing_path "$TARGET_ROOT/CLAUDE.md"
ln -s AGENTS.md "$TARGET_ROOT/CLAUDE.md"

(
  cd "$TARGET_ROOT"
  uv sync --all-extras --group dev
  uv run poe lint_full
  uv run poe test
)

printf 'Bootstrapped downstream repo in %s\n' "$TARGET_ROOT"
