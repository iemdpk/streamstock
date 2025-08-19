#!/bin/bash

# Ask user for branch name (also used as commit message)
read -p "Enter branch name (commit message will be same): " BRANCH

# Add all changes
git add ./

# Create new branch and switch to it
git checkout -b "$BRANCH"

# Commit changes
git commit -m "$BRANCH"

# Push branch to remote
git push -u origin "$BRANCH"

echo "Branch '$BRANCH' created, committed, and pushed successfully!"
