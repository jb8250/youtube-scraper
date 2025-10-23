from flask import Flask, request, jsonify
from YouTube_Search_Scraper import YouTubeSearchScraper, CONFIG, YOUTUBE_CONFIG, DATE_FORMATS
import json

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    search_term = data.get('searchTerm')

    if not search_term:
        return jsonify({'error': 'searchTerm is required'}), 400

    SEARCH_CONFIG = {
        'term': search_term,
        'title_filter': True,
        'configured': True
    }

    scraper = YouTubeSearchScraper(headless=True, debug=False, search_config=SEARCH_CONFIG)
    videos = scraper.search_youtube(max_videos=CONFIG['max_videos'])
    
    links = [video['url'] for video in videos]

    return jsonify({'links': links})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)