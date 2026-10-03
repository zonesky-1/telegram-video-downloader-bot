#!/usr/bin/env python3
"""
LokLok Streaming Platform Scraper
Search and stream films/series from lokal.com (LokLok)
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
import json
from typing import List, Dict, Optional


class LokLokStreamingScraper:
    """Scraper for LokLok streaming platform - films and series"""
    
    BASE_URL = "https://www.loklok.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.loklok.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def search_movies(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for movies/films on LokLok"""
        search_url = f"{self.BASE_URL}/cari?q={quote(query)}"
        
        try:
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                # Try alternative search endpoint
                search_url = f"{self.BASE_URL}/search?q={quote(query)}"
                response = self.session.get(search_url, timeout=15)
            
            return self._parse_search_results(response.text, query)
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def _parse_search_results(self, html: str, query: str) -> List[Dict]:
        """Parse search results from HTML"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Try to find video/items in various possible structures
        items = []
        
        # Method 1: Find __NEXT_DATA__ for Next.js SSR
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data and next_data.string:
            try:
                data = json.loads(next_data.string)
                items = self._extract_from_next_data(data)
            except:
                pass
        
        # Method 2: Find video links in grid/list
        if not items:
            # Look for video cards
            for card in soup.find_all('a', href=True):
                href = card['href']
                if '/i/' in href or '/movie/' in href or '/series/' in href:
                    title_elem = card.find(['h3', 'h2', 'h4']) or card.find(class_=re.compile(r'title|name', re.I))
                    title = title_elem.get_text(strip=True) if title_elem else card.get_text(strip=True)[:100]
                    
                    items.append({
                        'title': title,
                        'url': urljoin(self.BASE_URL, href),
                        'thumbnail': card.find('img')['src'] if card.find('img') else ''
                    })
        
        # Method 3: Look for data attributes
        for div in soup.find_all('div', {'data-video': True, 'data-id': True}):
            video_id = div.get('data-id')
            title = div.get('data-title') or div.find('h3').get_text() if div.find('h3') else 'Unknown'
            url = f"{self.BASE_URL}/i/{video_id}"
            
            items.append({
                'title': title,
                'url': url,
                'thumbnail': div.get('data-thumbnail', '')
            })
        
        return items[:max_results]
    
    def _extract_from_next_data(self, data: dict) -> List[Dict]:
        """Extract video data from Next.js __NEXT_DATA__"""
        items = []
        
        try:
            # Navigate different possible data structures
            page_props = data.get('props', {}).get('pageProps', {})
            
            # Try different keys
            for key in ['videos', 'movies', 'items', 'results', 'data']:
                if key in page_props:
                    items_data = page_props[key]
                    if isinstance(items_data, list):
                        for item in items_data:
                            items.append({
                                'title': item.get('title') or item.get('name') or 'Unknown',
                                'url': item.get('url') or f"{self.BASE_URL}/i/{item.get('id')}",
                                'thumbnail': item.get('thumbnail') or item.get('image') or ''
                            })
                    elif isinstance(items_data, dict):
                        for key2, val in items_data.items():
                            if isinstance(val, list):
                                for item in val:
                                    items.append({
                                        'title': item.get('title') or item.get('name') or 'Unknown',
                                        'url': item.get('url') or f"{self.BASE_URL}/i/{item.get('id')}",
                                        'thumbnail': item.get('thumbnail') or item.get('image') or ''
                                    })
        except:
            pass
        
        return items
    
    def get_movie_info(self, url: str) -> Dict:
        """Get detailed information about a movie/series"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return self._parse_movie_page(response.text, url)
        except Exception as e:
            print(f"❌ Error getting movie info: {e}")
        
        return {}
    
    def _parse_movie_page(self, html: str, url: str) -> Dict:
        """Parse movie/series page"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract from __NEXT_DATA__
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data and next_data.string:
            try:
                data = json.loads(next_data.string)
                return self._parse_movie_data(data, url)
            except:
                pass
        
        # Fallback to HTML parsing
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'Unknown'
        description = soup.find('p').get_text(strip=True)[:500] if soup.find('p') else ''
        
        # Find streaming link
        video_src = None
        for script in soup.find_all('script'):
            if script.string:
                match = re.search(r'(?:source|video|url)\s*[:=]\s*["\']([^"\']+)', script.string)
                if match:
                    video_src = match.group(1)
                    break
        
        return {
            'title': title,
            'description': description,
            'streaming_url': video_src or url,
            'details_url': url
        }
    
    def _parse_movie_data(self, data: dict, url: str) -> Dict:
        """Parse movie data structure from Next.js"""
        try:
            page_props = data.get('props', {}).get('pageProps', {})
            movie_data = page_props.get('video', page_props.get('movie', page_props.get('data', {})))
            
            if not movie_data:
                movie_data = page_props.get('state', {}).get('video', {})
            
            return {
                'title': movie_data.get('title') or movie_data.get('name') or 'Unknown',
                'description': movie_data.get('description', movie_data.get('overview', ''))[:500],
                'year': movie_data.get('year'),
                'duration': movie_data.get('duration', 0),
                'rating': movie_data.get('rating', 'N/A'),
                'streaming_url': movie_data.get('streaming_url') or movie_data.get('url') or url,
                'details_url': url
            }
        except:
            return {}
    
    def browse_categories(self) -> Dict[str, List[str]]:
        """Browse available categories/genres"""
        categories = {
            'Action': f"{self.BASE_URL}/genre/action",
            'Comedy': f"{self.BASE_URL}/genre/comedy",
            'Drama': f"{self.BASE_URL}/genre/drama",
            'Horror': f"{self.BASE_URL}/genre/horror",
            'Romance': f"{self.BASE_URL}/genre/romance",
            'Sci-Fi': f"{self.BASE_URL}/genre/sci-fi",
            'Anime': f"{self.BASE_URL}/genre/anime",
            'Latest': f"{self.BASE_URL}/latest"
        }
        return categories
    
    def get_latest_releases(self, limit: int = 10) -> List[Dict]:
        """Get latest uploaded movies/series"""
        try:
            response = self.session.get(f"{self.BASE_URL}/latest", timeout=15)
            if response.status_code == 200:
                return self._parse_search_results(response.text, 'latest')[:limit]
        except Exception as e:
            print(f"❌ Error getting latest: {e}")
        
        return []


if __name__ == "__main__":
    scraper = LokLokStreamingScraper()
    
    print("🔍 LokLok Streaming Scraper\n")
    
    # Test search
    print("1. Testing search for 'Spiderman':")
    results = scraper.search_movies("Spiderman", max_results=3)
    for i, item in enumerate(results, 1):
        print(f"   {i}. {item.get('title', 'Unknown')}")
        print(f"      URL: {item.get('url', 'N/A')}")
    
    print("\n2. Listing categories:")
    categories = scraper.browse_categories()
    for cat, url in list(categories.items())[:5]:
        print(f"   📂 {cat}")
    
    print("\n3. Testing movie info extraction:")
    test_url = "https://lokal.com/i/7k714d0e"
    info = scraper.get_movie_info(test_url)
    print(f"   Title: {info.get('title', 'N/A')}")
    print(f"   Streaming URL: {info.get('details_url', 'N/A')}")