#!/bin/bash

# Cleanup script to remove venv files and logs

# Remove virtual environment directories
echo "Removing virtual environment directories..."
rm -rf venv/
rm -rf .venv/
rm -rf env/
rm -rf .env/

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Remove log files
echo "Removing log files..."
find . -type f -name "*.log" -exec rm -f {} +
rm -f logs.txt

# Remove .DS_Store files (macOS)
echo "Removing .DS_Store files..."
find . -type f -name ".DS_Store" -exec rm -f {} +

# Remove __pycache__ directories in src
echo "Removing __pycache__ directories in src..."
rm -rf src/__pycache__/

echo "Cleanup complete!"