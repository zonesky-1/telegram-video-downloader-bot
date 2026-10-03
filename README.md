# Telegram Video Downloader Bot

A Telegram bot that downloads videos from YouTube and other platforms with resolution selection, using fast aria2c engine.

## Features

- 📥 Supports YouTube, TikTok, Instagram, Facebook, Twitter, Reddit, and 30+ more platforms
- 🎬 Resolution selection (1080p, 720p, 480p, 360p, Audio, Best)
- ⚡ Ultra-fast downloads using aria2c (multi-connection)
- 📤 Auto-send video to your chat after download
- 🧹 Automatic cleanup after sending

## Requirements

- Python 3.10+
- aiogram (Telegram Bot API framework)
- yt-dlp (video downloading)
- aria2 (fast download engine)

## Installation

```bash
# Clone or download this folder
git clone https://github.com/your-repo/telegram-video-bot.git
cd telegram-video-bot

# Run setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install aiogram yt-dlp

# Install aria2
sudo apt install aria2  # Ubuntu/Debian
# or: brew install aria2  # macOS
```

## Configuration

1. Create a bot with [BotFather](https://t.me/BotFather) on Telegram
2. Get your bot token
3. Edit `bot.py` and replace `YOUR_BOT_TOKEN_HERE` with your token

```python
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
```

Or set environment variable:
```bash
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
```

## Usage

```bash
# Run the bot
source .venv/bin/activate
python bot.py
```

Then in Telegram:
1. Send `/start` to initialize
2. Send `/help` for instructions
3. Send any video URL (YouTube, TikTok, etc.)
4. Click your preferred resolution
5. Wait for download and receive the video

## Development

### Project Structure

```
telegram_video_bot/
├── bot.py              # Main bot code
├── setup.sh            # Installation script
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── systemd/            # Optional systemd service files
    └── video-bot.service
```

### Architecture

```
┌─────────────┐
│   Telegram  │
│     Bot     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   yt-dlp    │──► Extract video metadata
└──────┬──────┘
       │
       ▼
┌─────────────┐   ┌─────────────┐
│   aria2c    │──►│ Download    │
│ (fast engine) │  │ to temp dir │
└─────────────┘   └──────┬──────┘
                       │
                       ▼
┌─────────────┐   ┌─────────────┐
│   FFmpeg    │──►│ Postproc &  │
│             │   │ Metadata    │
└─────────────┘   └──────┬──────┘
                       │
                       ▼
┌─────────────┐
│   Telegram  │
│   Chat      │
└─────────────┘
```

### Key Components

1. **VideoExtractionHandler** - Extracts video info using yt-dlp
2. **ResolutionKeyboard** - Shows resolution selection buttons
3. **VideoDownloader** - Downloads with yt-dlp + aria2c
4. **VideoSender** - Sends video via Telegram Bot API
5. **CleanupManager** - Removes temp files after sending

## Performance

- aria2c provides multi-connection downloads (up to 16 connections)
- Default chunk size: 1MB
- Timeout: 60 seconds
- Ideal for large files (200MB+)

## Supported Platforms

- YouTube
- TikTok
- Instagram
- Facebook
- Twitter/X
- Reddit
- Vimeo
- Dailymotion
- And 30+ more via yt-dlp

## License

MIT License - Feel free to modify and distribute

## Author

Created for Telegram Video Downloader Bot similar to LokLok bot