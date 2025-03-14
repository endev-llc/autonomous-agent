import os
import json
import markdown
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from loguru import logger
from database import ArticleDatabase

app = Flask(__name__, 
            static_folder="../web",
            template_folder="../web")
db = ArticleDatabase()

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the web folder"""
    return send_from_directory(app.static_folder, path)

@app.route('/api/articles/recent')
def recent_articles():
    """Get recent articles from the database"""
    limit = int(request.args.get('limit', 20))
    articles = db.get_recent_articles(limit=limit)
    
    # Format articles for display
    for article in articles:
        article['formatted_date'] = format_date(article.get('publication_date', ''))
        article['formatted_summary'] = markdown.markdown(article.get('summary', ''))
        
        # Format keywords as a list if it's a string
        if isinstance(article.get('keywords'), str):
            try:
                article['keywords'] = json.loads(article['keywords'])
            except:
                article['keywords'] = []
    
    return jsonify(articles)

@app.route('/api/articles/search')
def search_articles():
    """Search for articles by query"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    limit = int(request.args.get('limit', 20))
    articles = db.search_articles(query, limit=limit)
    
    # Format articles for display
    for article in articles:
        article['formatted_date'] = format_date(article.get('publication_date', ''))
        article['formatted_summary'] = markdown.markdown(article.get('summary', ''))
        
        # Format keywords as a list if it's a string
        if isinstance(article.get('keywords'), str):
            try:
                article['keywords'] = json.loads(article['keywords'])
            except:
                article['keywords'] = []
    
    return jsonify(articles)

@app.route('/api/stats')
def get_stats():
    """Get recent statistics"""
    days = int(request.args.get('days', 7))
    stats = db.get_statistics(days=days)
    
    # Simple formatting for display
    for stat in stats:
        stat['formatted_date'] = format_date(stat.get('date', ''))
        
        # Format top_keywords as a list if it's a string
        if isinstance(stat.get('top_keywords'), str):
            try:
                stat['top_keywords'] = json.loads(stat['top_keywords'])
            except:
                stat['top_keywords'] = []
    
    return jsonify(stats)

@app.route('/api/keywords')
def get_keywords():
    """Get all unique keywords for filtering"""
    articles = db.get_recent_articles(limit=1000)  # Increased limit to get more keywords
    
    all_keywords = set()
    for article in articles:
        keywords = article.get('keywords', [])
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except:
                keywords = []
        
        if isinstance(keywords, list):
            all_keywords.update(keywords)
    
    return jsonify(sorted(list(all_keywords)))

def format_date(date_str):
    """Format a date string for display"""
    if not date_str:
        return "Unknown date"
    
    try:
        if 'T' in date_str:
            # Handle ISO format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y")
        else:
            # Try a simple date format
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%B %d, %Y")
    except:
        return date_str  # Return original if parsing fails

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask web server"""
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # This allows for running the web server directly
    logger.info("Starting web server")
    run_server(debug=True)
