#!/bin/bash
# Setup script for Telegram Video Downloader Bot

echo "🚀 Setting up Telegram Video Downloader Bot..."

# Check if venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing Python packages..."
pip install -q aiogram yt-dlp

# Check aria2c
if ! command -v aria2c &> /dev/null; then
    echo "⚠️  aria2c not found. Installing..."
    sudo apt update && sudo apt install -y aria2
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit bot.py and set your BOT_TOKEN"
echo "2. Run: source .venv/bin/activate && python bot.py"
echo ""
echo "📝 Or use the systemd service file for auto-start"