#!/usr/bin/env python3
"""
Telegram Video Downloader Bot
Similar to LokLok bot - allows downloading videos with resolution selection
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)
from aiogram.filters import Command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Bot Token here
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Download settings
DOWNLOAD_FOLDER = Path("/tmp/video_downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

# Resolution mapping
RESOLUTIONS = {
    "best": ("Best Quality", "bestvideo+bestaudio/best"),
    "1080p": ("1080p HD", "bestvideo[height<=1080]+bestaudio/best"),
    "720p": ("720p HD", "bestvideo[height<=720]+bestaudio/best"),
    "480p": ("480p SD", "bestvideo[height<=480]+bestaudio/best"),
    "360p": ("360p LD", "bestvideo[height<=360]+bestaudio/best"),
    "audio": ("Audio Only", "bestaudio")
}


class VideoDownloadBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all message and callback handlers"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.answer(
                "🎬 Video Downloader Bot\n\n"
                "Send me a video link (YouTube, TikTok, Instagram, etc.) "
                "and I'll let you choose the resolution to download!"
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            await message.answer(
                "📖 How to use:\n"
                "1️⃣ Send any video link\n"
                "2️⃣ Choose resolution from buttons\n"
                "3️⃣ Bot downloads and sends video to you\n\n"
                "**Supported:** YouTube, TikTok, Instagram, Facebook, Twitter, Reddit, and more!"
            )
        
        @self.dp.message(F.text.regexp(r'https?://'))
        async def handle_video_link(message: Message):
            """Handle video URL - extract info and show resolution options"""
            url = message.text.strip()
            
            try:
                await message.answer("⏳ Processing video info...")
                
                # Get video info using yt-dlp
                info = await self._get_video_info(url)
                
                # Create inline keyboard with resolution options
                kb = self._create_resolution_keyboard(info.get('id', 'unknown'))
                
                await message.answer(
                    f"🎬 {info.get('title', 'Unknown Title')}\n\n"
                    f"👤 {info.get('uploader', 'Unknown')}\n"
                    f"⏱️ {self._format_duration(info.get('duration', 0))}\n",
                    reply_markup=kb
                )
                
            except Exception as e:
                logger.error(f"Error getting video info: {e}")
                await message.answer(f"❌ Error: {str(e)}\nPlease try another link.")
        
        @self.dp.callback_query(lambda c: c.data.startswith("download_"))
        async def process_download(callback: CallbackQuery):
            """Handle resolution selection and download"""
            try:
                # Extract data from callback
                data = callback.data.split("_", 1)[1]
                parts = data.split(":")
                video_id = parts[0]
                resolution_key = parts[1] if len(parts) > 1 else "best"
                
                user_id = callback.from_user.id
                
                await callback.answer()
                await callback.message.edit_text("📥 Downloading with aria2 for fast speed...")
                
                # Download video using yt-dlp + aria2
                filepath = await self._download_video(video_id, resolution_key, user_id)
                
                # Send video
                await callback.message.edit_text("📤 Sending video...")
                await self._send_video(callback.message.chat.id, filepath, callback.message.message_id)
                
                # Cleanup
                if filepath.exists():
                    filepath.unlink()
                    
            except Exception as e:
                logger.error(f"Download error: {e}")
                try:
                    await callback.message.edit_text(f"❌ Download failed: {str(e)}")
                except:
                    await callback.message.answer(f"❌ Download failed: {str(e)}")
        
        # Store video info for download
        self.video_cache = {}
    
    async def _get_video_info(self, url: str) -> dict:
        """Extract video information using yt-dlp"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                'id': info.get('id', 'unknown'),
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', info.get('author', 'Unknown')),
                'duration': info.get('duration', 0),
                'webpage_url': info.get('webpage_url', url),
                'thumbnail': info.get('thumbnail'),
            }
    
    def _create_resolution_keyboard(self, video_id: str) -> InlineKeyboardMarkup:
        """Create inline keyboard with resolution options"""
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        
        for key, (label, _) in RESOLUTIONS.items():
            kb.add(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"download_{video_id}:{key}"
                )
            )
        
        return kb
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human readable format"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    async def _download_video(self, video_id: str, resolution_key: str, user_id: int) -> Path:
        """Download video using yt-dlp with aria2c as engine"""
        
        # Get format string
        _, format_str = RESOLUTIONS.get(resolution_key, RESOLUTIONS["best"])
        
        # Create temp directory for download
        temp_dir = DOWNLOAD_FOLDER / f"{user_id}_{video_id}"
        temp_dir.mkdir(exist_ok=True)
        
        # ytdlp options with aria2c
        ydl_opts = {
            'format': format_str,
            'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'subtitleslangs': [],
            'postprocessors': [
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
            ],
            # Use aria2c for download
            'external_downloader': 'aria2c',
            'external_downloader_args': [
                '-x16',      # 16 connections
                '-s16',      # 16 splits
                '-k1M',      # 1MB chunk size
                '--timeout=60',
                '--max-connection-per-server=16'
            ],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
        # Find downloaded file
        files = list(temp_dir.glob("*"))
        if files:
            video_file = files[0]
            # Move to final location
            final_path = DOWNLOAD_FOLDER / f"{video_id}_final.mp4"
            video_file.rename(final_path)
            temp_dir.rmdir()
            return final_path
        
        raise Exception("Download failed - no file produced")
    
    async def _send_video(self, chat_id: int, filepath: Path, message_id: int):
        """Send video file to user"""
        with open(filepath, 'rb') as video_file:
            await self.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                supports_streaming=True,
                caption="📥 Download complete! Delete this file when received."
            )
    
    async def run(self):
        """Run the bot"""
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)


if __name__ == "__main__":
    bot = VideoDownloadBot(BOT_TOKEN)
    asyncio.run(bot.run())