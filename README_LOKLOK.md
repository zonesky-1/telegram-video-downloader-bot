# LokLok Streaming Platform Scraper for Telegram Bot
Search and stream films and series from LokLok.id

## Features:
- 🔍 Search movies/films/series by keyword
- 🎬 Get detailed movie information (title, year, duration, rating)
- 📺 Browse streaming links for films and series
- 🏷️ Browse by categories/geners
- 🆕 Get latest releases

## Usage:

### Search movies
```python
scraper = LokLokStreamingScraper()
results = scraper.search_movies("Spiderman", max_results=10)
for movie in results:
    print(f"{movie['title']}: {movie['url']}")
```

### Get movie details
```python
info = scraper.get_movie_info("https://lokal.com/i/video-id")
print(f"Title: {info['title']}")
print(f"Streaming: {info.get('streaming_url', 'N/A')}")
```

### Browse categories
```python
categories = scraper.browse_categories()
for name, url in categories.items():
    print(f"{name}: {url}")
```

### Get latest releases
```python
latest = scraper.get_latest_releases(limit=10)
```

## Note:
LokLok is an Indonesian free streaming platform. This scraper:
1. Searches and lists available content (no download)
2. Extracts streaming URLs for legitimate viewing
3. Provides redirect links to official LokLok players

## Installation:
```bash
pip install requests beautifulsoup4 lxml
```

Made by Telegram -> @an0ym -> JOIN https://t.me/jailbreakall