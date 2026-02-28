#!/bin/zsh

# ── Git Initial Push Script ───────────────────────────────────────────────────
# Place this file in your project root and run it once.
# Usage: bash git_init.sh

echo ""
echo "=== Git Initial Push Setup ==="
echo ""

# Ask for GitHub repo URL
echo "Paste your GitHub repository URL: " REPO_URL
read -r REPO_URL

if [ -z "$REPO_URL" ]; then
  echo "ERROR: No URL provided. Exiting."
  exit 1
fi

# Ask for commit message with a default
echo "Commit message [Initial commit]: " COMMIT_MSG
read -r COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-"Initial commit"}

# Run git commands
git init
git add .
git commit -m "$COMMIT_MSG"
git branch -M main
git remote add origin "$REPO_URL"
git push -u origin main

echo ""
echo "=== Done. Your code is on GitHub. ==="
echo ""
