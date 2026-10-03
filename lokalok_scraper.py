#!/usr/bin/env python3
"""
LokLok Video Scraper for Telegram Bot
Scrapes and downloads videos from LokLok.id platform
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from pathlib import Path

# Try to import yt-dlp via subprocess
import subprocess
import sys


class LokLokScraper:
    """Scraper for LokLok video platform"""
    
    BASE_URL = "https://lokal.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def extract_video_id(self, url):
        """Extract video ID from LokLok URL"""
        # LokLok URLs are typically: https://lokal.com/i/video-id
        pattern = r'lokal\.com/i/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    def get_video_info(self, url):
        """Get video information from LokLok URL"""
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid LokLok URL format")
        
        # Method 1: Try direct API endpoint
        api_url = f"https://api.lokal.com/v1/video/{video_id}"
        
        try:
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data)
        except Exception as e:
            print(f"API method failed: {e}")
        
        # Method 2: Scrape the page directly
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return self._scrape_page(response.text, video_id)
        except Exception as e:
            print(f"Scraping method failed: {e}")
        
        raise Exception("Could not extract video information")
    
    def _parse_api_response(self, data):
        """Parse API response into standard format"""
        return {
            'id': data.get('id', data.get('video_id', 'unknown')),
            'title': data.get('title', data.get('name', 'Unknown Video')),
            'uploader': data.get('author', {}).get('name', 'Unknown'),
            'duration': data.get('duration', 0),
            'url': data.get('url', ''),
            'thumbnail': data.get('thumbnail', {}).get('url', data.get('image', '')),
            'video_url': data.get('url', ''),
            'formats': self._extract_formats(data),
        }
    
    def _scrape_page(self, html_content, video_id):
        """Scrape video info from HTML page"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Look for video data in various possible locations
        # Method: Check for __NEXT_DATA__ or similar script tags
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            try:
                data = json.loads(next_data.string)
                return self._parse_next_data(data, video_id)
            except:
                pass
        
        # Method: Check for videoUrl in script tags
        video_url_pattern = r'"videoUrl"\s*:\s*"([^"]+)"'
        match = re.search(video_url_pattern, html_content)
        if match:
            video_url = match.group(1)
        
        # Extract title
        title_tag = soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else 'Unknown Video'
        
        # Extract uploader
        author_tag = soup.find(string=re.compile(r'@[\w]+', re.I))
        uploader = author_tag.strip() if author_tag else 'Unknown'
        
        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'duration': 0,
            'url': f"https://lokal.com/i/{video_id}",
            'thumbnail': '',
            'video_url': video_url if match else '',
            'formats': [{'format_id': 'best', 'url': video_url}] if match else []
        }
    
    def _parse_next_data(self, data, video_id):
        """Parse __NEXT_DATA__ JSON structure"""
        try:
            # Navigate the Next.js data structure
            page_data = data.get('props', {}).get('pageProps', {})
            video_data = page_data.get('video', page_data.get('data', {}))
            
            if not video_data:
                # Try alternative structure
                video_data = data.get('state', {}).get('video', {})
            
            return {
                'id': video_id,
                'title': video_data.get('title', 'Unknown Video'),
                'uploader': video_data.get('author', {}).get('name', 'Unknown'),
                'duration': video_data.get('duration', 0),
                'url': video_data.get('url', f"https://lokal.com/i/{video_id}"),
                'thumbnail': video_data.get('thumbnail', {}).get('url', ''),
                'video_url': video_data.get('url', ''),
                'formats': self._extract_formats(video_data),
            }
        except Exception as e:
            print(f"Error parsing Next.js data: {e}")
            raise
    
    def _extract_formats(self, data):
        """Extract available video formats"""
        formats = []
        
        # Check for different format sources
        if 'formats' in data:
            for fmt in data['formats']:
                formats.append({
                    'format_id': fmt.get('quality', 'unknown'),
                    'height': fmt.get('height', 0),
                    'width': fmt.get('width', 0),
                    'url': fmt.get('url', ''),
                    'fps': fmt.get('fps', 30),
                    'vcodec': fmt.get('codec', 'h264'),
                })
        
        # Add default format
        if not formats and 'video_url' in data:
            formats.append({
                'format_id': 'best',
                'height': 1080,
                'url': data['video_url']
            })
        
        return formats


def download_with_yt_dlp(url, output_path):
    """Download video using yt-dlp with aria2c"""
    import tempfile
    import subprocess
    
    # Install yt-dlp if not present in venv
    venv_python = "/home/agentuser/telegram_video_bot/.venv/bin/python"
    
    # Create a temporary script to run yt-dlp
    ydl_script = f"""
import yt_dlp
import sys

url = "{url}"
output = "{output_path}"

ydl_opts = {{
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': output,
    'quiet': True,
    'no_warnings': True,
    'writesubtitles': False,
    'postprocessors': [
        {{'key': 'FFmpegMetadata', 'add_metadata': True}},
    ],
    'external_downloader': 'aria2c',
    'external_downloader_args': [
        '-x16', '-s16', '-k1M', '--timeout=60', '--max-connection-per-server=16'
    ],
}}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
"""
    
    # Write script to temp file
    script_file = '/tmp/download_script.py'
    with open(script_file, 'w') as f:
        f.write(ydl_script)
    
    # Run with venv python
    result = subprocess.run([venv_python, script_file], capture_output=True, text=True)
    
    # Cleanup
    if os.path.exists(script_file):
        os.remove(script_file)
    
    return result.returncode == 0, result.stderr


if __name__ == "__main__":
    # Test the scraper
    scraper = LokLokScraper()
    
    # Example URL - replace with actual LokLok video
    test_url = "https://lokal.com/i/some-video-id"
    
    try:
        print("Testing LokLok scraper...")
        info = scraper.get_video_info("https://lokal.com/i/7k714d0e")
        print(f"✅ Video found: {info['title']}")
        print(f"   Uploader: {info['uploader']}")
        print(f"   ID: {info['id']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nNote: LokLok has anti-bot measures and may require:")
        print("  - Proper referer headers")
        print("  - User-agent spoofing")
        print("  - Cookie handling")
        print("  - Bypassing CDN protection")