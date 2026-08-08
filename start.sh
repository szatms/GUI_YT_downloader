#!/bin/bash

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install requirements if not already installed
if ! pip list | grep -q yt_dlp; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run the application in background to free up terminal
echo "Starting YouTube Downloader GUI..."
python youtube_downloader_gui.py "$@" &

# Deactivate virtual environment
deactivate