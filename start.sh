#!/bin/bash
set -e

echo "Installing ffmpeg..."
apt-get update && apt-get install -y ffmpeg

echo "Starting application..."
python subliminal_master.py
