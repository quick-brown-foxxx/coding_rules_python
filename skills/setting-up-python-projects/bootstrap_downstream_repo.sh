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
# Rendered layout (PACKAGE_NAME defaults to todo_package_name):
#   src/PACKAGE_NAME/                     product package (shipped in the wheel)
#   src/PACKAGE_NAME/shared/              runtime building blocks (logging, shortcuts)
#   tools/linting/                        dev-only custom lint checks (not shipped)
#   shared_tests/                         tests for the copied shared/tools code
#   tests/                                project's own tests
#   docs/coding_rules.md
#
# Top-level `shared` no longer ships as its own wheel package, so wheel-based
# installs (pip, uv tool install, uvx) do not collide with a generic `shared`.
#
# It promotes template files into place, copies the shared runtime modules,
# tools/linting and shared_tests, creates the CLAUDE.md symlink, then runs:
#   uv sync
#   uv run poe lint_full
#   uv run poe test
#
# Usage: %s [--package-name NAME] [SOURCE_REPO] TARGET_REPO
#   --package-name NAME: import package name (default: todo_package_name)
#   SOURCE_REPO: local checkout path or upstream URL (defaults to GitHub)
#   TARGET_REPO : destination directory for the new project
#
# GNU/Linux-first bootstrap helper: `realpath -m` lets us normalize a target
# path that may not exist yet. Broaden this when the bootstrap needs other
# platforms.

DEFAULT_SOURCE="https://github.com/quick-brown-foxxx/coding_rules_python.git"
DEFAULT_PACKAGE_NAME="todo_package_name"

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
  mkdir -p "$(dirname "$target_path")"
  cp -R "$source_path" "$target_path"
}

render_text_files() {
  local target_root="$1"
  local package_name="$2"

  find "$target_root" -type f \( \
    -name '*.py' -o -name '*.toml' -o -name '*.md' \
    -o -name '*.yaml' -o -name '*.yml' -o -name '*.json' \
  \) -print0 | xargs -0 sed -E -i \
    -e "s/todo_package_name/$package_name/g" \
    -e "s/(^|[^A-Za-z0-9_.])shared\.logging/\1$package_name.shared.logging/g" \
    -e "s/(^|[^A-Za-z0-9_.])shared\.shortcuts/\1$package_name.shared.shortcuts/g"
}

print_usage() {
  printf 'Usage: %s [--package-name NAME] [SOURCE_REPO] TARGET_REPO\n' "$0"
  printf '  --package-name NAME: import package name (default: %s)\n' "$DEFAULT_PACKAGE_NAME"
  printf '  SOURCE_REPO: local checkout path or upstream URL (default: %s)\n' "$DEFAULT_SOURCE"
  printf '  TARGET_REPO : destination directory for the new project\n'
}

show_help() {
  print_usage
  exit 0
}

usage() {
  print_usage >&2
  exit 1
}

is_reserved_word() {
  case "$1" in
    False | None | True | and | as | assert | async | await | break | class | continue | def | del | elif | else | \
      except | finally | for | from | global | if | import | in | is | lambda | nonlocal | not | or | pass | raise | \
      return | try | while | with | yield)
      return 0
      ;;
    *) return 1 ;;
  esac
}

PACKAGE_NAME="$DEFAULT_PACKAGE_NAME"
POSITIONAL=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --package-name)
      [ "$#" -ge 2 ] || usage
      PACKAGE_NAME="$2"
      shift 2
      ;;
    --package-name=*)
      PACKAGE_NAME="${1#*=}"
      shift
      ;;
    -h | --help)
      show_help
      ;;
    --)
      shift
      POSITIONAL+=("$@")
      break
      ;;
    -*)
      usage
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [ "${#POSITIONAL[@]}" -lt 1 ] || [ "${#POSITIONAL[@]}" -gt 2 ]; then
  usage
fi

if [[ ! "$PACKAGE_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  printf 'Invalid package name: %s (use a Python identifier)\n' "$PACKAGE_NAME" >&2
  exit 1
fi

if is_reserved_word "$PACKAGE_NAME"; then
  printf 'Invalid package name: %s (Python keyword)\n' "$PACKAGE_NAME" >&2
  exit 1
fi

SOURCE_ARG="${POSITIONAL[0]}"
TARGET_ARG="${POSITIONAL[1]:-}"

# One positional argument means: default source, that argument is the target.
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

copy_directory "$SOURCE_ROOT/templates/src/todo_package_name" "$TARGET_ROOT/src/$PACKAGE_NAME"
copy_directory "$SOURCE_ROOT/shared/logging" "$TARGET_ROOT/src/$PACKAGE_NAME/shared/logging"
copy_directory "$SOURCE_ROOT/shared/shortcuts" "$TARGET_ROOT/src/$PACKAGE_NAME/shared/shortcuts"
copy_file "$SOURCE_ROOT/shared/__init__.py" "$TARGET_ROOT/src/$PACKAGE_NAME/shared/__init__.py"

copy_directory "$SOURCE_ROOT/tools/linting" "$TARGET_ROOT/tools/linting"
copy_file "$SOURCE_ROOT/tools/__init__.py" "$TARGET_ROOT/tools/__init__.py"

copy_directory "$SOURCE_ROOT/shared_tests" "$TARGET_ROOT/shared_tests"

copy_file "$SOURCE_ROOT/templates/AGENTS.md" "$TARGET_ROOT/AGENTS.md"
copy_file "$SOURCE_ROOT/templates/pyproject.toml" "$TARGET_ROOT/pyproject.toml"
copy_file "$SOURCE_ROOT/templates/pre-commit-config.yaml" "$TARGET_ROOT/.pre-commit-config.yaml"
copy_directory "$SOURCE_ROOT/templates/tests" "$TARGET_ROOT/tests"
copy_file "$SOURCE_ROOT/templates/gitignore" "$TARGET_ROOT/.gitignore"
copy_file "$SOURCE_ROOT/templates/vscode_settings.json" "$TARGET_ROOT/.vscode/settings.json"
copy_file "$SOURCE_ROOT/templates/vscode_extensions.json" "$TARGET_ROOT/.vscode/extensions.json"

copy_file "$SOURCE_ROOT/rules/coding_rules.md" "$TARGET_ROOT/docs/coding_rules.md"

require_missing_path "$TARGET_ROOT/CLAUDE.md"
ln -s AGENTS.md "$TARGET_ROOT/CLAUDE.md"

render_text_files "$TARGET_ROOT" "$PACKAGE_NAME"

(
  cd "$TARGET_ROOT"
  uv sync
  uv run poe lint_full
  uv run poe test
)

printf 'Bootstrapped downstream repo in %s\n' "$TARGET_ROOT"
