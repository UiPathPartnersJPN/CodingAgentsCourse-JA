#!/usr/bin/env bash
#
# bootstrap-framework.sh
# Pulls the reusable authoring framework from the base Agentic Practice repo
# into this course repo, so we don't duplicate (or drift from) the proven setup.
#
# Copies: Master/, .claude/commands/, hooks/, scripts/, stylesheets, javascripts.
# Does NOT touch: docs/ content, mkdocs.yml, main.py, CLAUDE.md, README — those are
# course-specific and already configured here.
#
# Safe to re-run. Review the diff afterwards before committing.

set -euo pipefail

BASE_REPO="https://github.com/uipath-practice/AgenticPracticeCourse.git"
TMP="$(mktemp -d)"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "Cloning base framework into a temp dir..."
git clone --depth 1 "$BASE_REPO" "$TMP"

echo "Copying reusable framework files..."
# Authoring rules & templates
cp -R "$TMP/Master/." "$HERE/Master/"
# Claude Code authoring commands
mkdir -p "$HERE/.claude/commands"
cp -R "$TMP/.claude/commands/." "$HERE/.claude/commands/"
# Two-column layout hook
cp -R "$TMP/hooks/." "$HERE/hooks/" 2>/dev/null || true
# Screenshot metadata pipeline
cp -R "$TMP/scripts/." "$HERE/scripts/" 2>/dev/null || true
# Shared CSS / JS
cp "$TMP/docs/stylesheets/extra.css" "$HERE/docs/stylesheets/extra.css" 2>/dev/null || true
cp "$TMP/docs/javascripts/extra.js"  "$HERE/docs/javascripts/extra.js"  2>/dev/null || true
# Logo / favicon (replace later if needed)
cp "$TMP/docs/assets/images/"*ogo* "$HERE/docs/assets/images/" 2>/dev/null || true
cp "$TMP/docs/assets/images/favicon".* "$HERE/docs/assets/images/" 2>/dev/null || true

rm -rf "$TMP"

echo ""
echo "Done. Review what changed:"
echo "  git status"
echo ""
echo "Note: the screenshot pipeline (scripts/) needs scripts/.env with Azure OpenAI"
echo "credentials — see Master/HOWTO.md. CLI/KB-driven lessons do not require it."
