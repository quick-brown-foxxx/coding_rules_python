#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
  printf 'Usage: %s SOURCE_REPO TARGET_REPO\n' "$0" >&2
  exit 1
fi

# GNU/Linux-first bootstrap helper: `realpath -m` lets us normalize a target path
# that may not exist yet. Broaden this when the bootstrap needs other platforms.
SOURCE_ROOT=$(realpath "$1")
TARGET_ROOT=$(realpath -m "$2")

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

mkdir -p "$TARGET_ROOT"

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
copy_file "$SOURCE_ROOT/PHILOSOPHY.md" "$TARGET_ROOT/docs/PHILOSOPHY.md"

require_missing_path "$TARGET_ROOT/CLAUDE.md"
ln -s AGENTS.md "$TARGET_ROOT/CLAUDE.md"

(
  cd "$TARGET_ROOT"
  uv sync --all-extras --group dev
  uv run poe lint_full
  uv run poe test
)

printf 'Bootstrapped downstream repo in %s\n' "$TARGET_ROOT"
