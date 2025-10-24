import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode, urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configuration settings
CONFIG = {
    'debug': False,
    'max_videos': 100,  # Maximum videos to collect
    'headless': True,
    'scroll_pause_time': 2.0,
    'max_videos_per_search': 50,
    'page_load_timeout': 30,
    'implicit_wait': 10,
}

# YouTube search configuration
YOUTUBE_CONFIG = {
    'base_url': 'https://www.youtube.com',
    'search_path': '/results',
    'today_filter': 'CAISBAgBEAE%253D',
    'video_selector': 'ytd-video-renderer,ytd-grid-video-renderer',
    'title_selector': '#video-title',
    'channel_selector': '#channel-name,#text',
    'duration_selector': '#text.ytd-thumbnail-overlay-time-status-renderer',
    'views_selector': '#metadata-line span:nth-child(1)',
    'upload_time_selector': '#metadata-line span:nth-child(2)',
}

# Date formats for search terms
DATE_FORMATS = [
    '%m/%d/%Y',  # 10/19/2023
    '%m-%d-%Y',  # 10-19-2023
    '%B %d, %Y', # October 19, 2023
    '%b %d, %Y', # Oct 19, 2023
    '%Y-%m-%d',  # 2023-10-19
]

class YouTubeSearchScraper:
    """YouTube scraper for any search term"""

    def __init__(self, headless: bool = True, debug: bool = False, search_config: Optional[Dict] = None):
        self.headless = headless
        self.debug = debug
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.search_config = search_config or {'term': '', 'title_filter': True}

        # Configure logging
        if debug:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def setup_driver(self) -> None:
        """Configure and initialize Chrome WebDriver for Colab"""
        try:
            chrome_options = Options()

            # Colab-specific options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')

            if self.headless:
                chrome_options.add_argument('--headless')

            # Set binary location for Colab
            chrome_options.binary_location = '/usr/bin/chromium-browser'

            # Anti-detection measures
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Window size
            chrome_options.add_argument('--window-size=1920,1080')

            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)

            # Set timeouts
            self.driver.set_page_load_timeout(CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(CONFIG['implicit_wait'])

            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.logger.info("Chrome driver initialized successfully for Colab")

        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            raise

    def cleanup(self) -> None:
        """Close browser and cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def get_default_search_terms(self) -> List[str]:
        """Get search term directly from user input"""
        # Return a list containing only the exact search term
        return [self.search_config['term']]

    def build_search_url(self, search_term: str) -> str:
        """Build YouTube search URL with 'Today' filter"""
        base_url = f"{YOUTUBE_CONFIG['base_url']}{YOUTUBE_CONFIG['search_path']}"

        params = {
            'search_query': search_term,
            'sp': YOUTUBE_CONFIG['today_filter']  # Today filter
        }

        return f"{base_url}?{urlencode(params)}"

    def scroll_for_videos(self, target_count: int, max_scrolls: int = 10) -> bool:
        """Scroll down to load more videos. Returns True if target reached."""
        if not self.driver:
            return False

        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

            # Wait for new content to load
            time.sleep(CONFIG['scroll_pause_time'])

            # Check if we've reached target count
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, YOUTUBE_CONFIG['video_selector'])
            if len(video_elements) >= target_count:
                self.logger.info(f"Reached target video count: {len(video_elements)}")
                return True

            # Check if page height changed
            new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                self.logger.info("No more content to load")
                break

            last_height = new_height
            scrolls += 1
            self.logger.debug(f"Scroll {scrolls}, videos found: {len(video_elements)}")

        return False

    def extract_video_data(self, video_element) -> Optional[Dict[str, Any]]:
        """Extract video data from a video element"""
        try:
            # Extract URL
            title_link = video_element.find_element(By.CSS_SELECTOR, YOUTUBE_CONFIG['title_selector'])
            url = title_link.get_attribute('href')

            if not url or 'watch?v=' not in url:
                return None

            # Extract title
            title = title_link.get_attribute('title') or title_link.text.strip()

            # Check if title contains the search term (case insensitive) - only if filter is enabled
            if self.search_config['title_filter']:
                title_lower = title.lower()
                search_term_lower = self.search_config['term'].lower()
                if search_term_lower not in title_lower:
                    return None  # Skip videos that don't mention the search term in title

            # Extract channel
            try:
                channel_element = video_element.find_element(By.CSS_SELECTOR, YOUTUBE_CONFIG['channel_selector'])
                channel = channel_element.text.strip()
            except NoSuchElementException:
                channel = "Unknown"

            # Extract duration
            try:
                duration_element = video_element.find_element(By.CSS_SELECTOR, YOUTUBE_CONFIG['duration_selector'])
                duration = duration_element.text.strip()
            except NoSuchElementException:
                duration = "Unknown"

            # Extract views and upload time
            try:
                metadata_elements = video_element.find_elements(By.CSS_SELECTOR, '#metadata-line span')
                views = metadata_elements[0].text.strip() if len(metadata_elements) > 0 else "Unknown"
                upload_time = metadata_elements[1].text.strip() if len(metadata_elements) > 1 else "Unknown"
            except (NoSuchElementException, IndexError):
                views = "Unknown"
                upload_time = "Unknown"

            # Extract video ID from URL
            parsed_url = urlparse(url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]

            if not video_id:
                return None

            return {
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'title': title,
                'channel': channel,
                'duration': duration,
                'views': views,
                'upload_time': upload_time,
                'scraped_at': datetime.now().isoformat(),
                'search_term': getattr(self, '_current_search_term', 'Unknown'),
                'filter_term': self.search_config['term']
            }

        except Exception as e:
            self.logger.debug(f"Error extracting video data: {e}")
            return None

    def scrape_search_term(self, search_term: str, max_videos: int) -> List[Dict[str, Any]]:
        """Scrape videos for a specific search term"""
        self._current_search_term = search_term
        videos = []

        try:
            # For date-based searches, don't use the "Today" filter
            if any(date_str in search_term.lower() for date_str in [
                datetime.now().strftime(fmt).lower() for fmt in DATE_FORMATS
            ]):
                # Use regular search without "Today" filter for date-specific searches
                search_url = f"{YOUTUBE_CONFIG['base_url']}{YOUTUBE_CONFIG['search_path']}?search_query={search_term}"
            else:
                # Use "Today" filter for general searches
                search_url = self.build_search_url(search_term)

            self.logger.info(f"Searching: {search_term}")

            self.driver.get(search_url)

            # Wait for initial results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, YOUTUBE_CONFIG['video_selector']))
            )

            # Scroll to load more videos
            self.scroll_for_videos(max_videos)

            # Extract video data
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, YOUTUBE_CONFIG['video_selector'])

            for element in video_elements[:max_videos]:
                video_data = self.extract_video_data(element)
                if video_data:
                    videos.append(video_data)

            self.logger.info(f"Found {len(videos)} videos matching '{search_term}'")

        except TimeoutException:
            self.logger.warning(f"Timeout loading search results for '{search_term}'")
        except Exception as e:
            self.logger.error(f"Error scraping '{search_term}': {e}")

        return videos

    def search_youtube(self, search_terms: Optional[List[str]] = None, max_videos: int = 50) -> List[Dict[str, Any]]:
        """Main search method - search YouTube for content matching the search term"""
        if not self.driver:
            self.setup_driver()

        if search_terms is None:
            search_terms = self.get_default_search_terms()

        all_videos = []
        seen_urls = set()

        self.logger.info(f"Starting scrape with search term: '{self.search_config['term']}', max {max_videos} videos total")

        for term in search_terms:
            if len(all_videos) >= max_videos:
                break

            remaining = max_videos - len(all_videos)
            term_videos = self.scrape_search_term(term, CONFIG['max_videos_per_search'])

            # Filter out duplicates
            for video in term_videos:
                if video['url'] not in seen_urls and len(all_videos) < max_videos:
                    all_videos.append(video)
                    seen_urls.add(video['url'])

            # Small delay between searches to be respectful
            time.sleep(1)

        self.logger.info(f"Scraping complete. Found {len(all_videos)} unique videos")
        return all_videos

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

print("✅ YouTubeSearchScraper class defined!")