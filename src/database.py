import os
import sqlite3
import json
from datetime import datetime
from loguru import logger

class ArticleDatabase:
    def __init__(self, db_path="data/articles.db"):
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.initialize_database()
        logger.info(f"Database initialized at {db_path}")
    
    def get_connection(self):
        """Create and return a database connection"""
        return sqlite3.connect(self.db_path)
    
    def initialize_database(self):
        """Create the database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create articles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                publication_date TEXT,
                discovery_date TEXT NOT NULL,
                summary TEXT,
                score REAL,
                keywords TEXT,
                content_snippet TEXT,
                processed BOOLEAN DEFAULT FALSE
            )
            ''')
            
            # Create statistics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                articles_found INTEGER,
                articles_processed INTEGER,
                avg_score REAL,
                top_keywords TEXT
            )
            ''')
            
            conn.commit()
    
    def add_article(self, article_data):
        """Add a new article to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if article already exists by URL
                cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data['url'],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"Article already exists in database: {article_data['title']}")
                    return False
                
                # Set discovery date if not provided
                if 'discovery_date' not in article_data:
                    article_data['discovery_date'] = datetime.now().isoformat()
                
                # Convert keywords list to JSON string if it's a list
                if 'keywords' in article_data and isinstance(article_data['keywords'], list):
                    article_data['keywords'] = json.dumps(article_data['keywords'])
                
                # Insert article into database
                cursor.execute('''
                INSERT INTO articles (
                    title, url, source, publication_date, discovery_date,
                    summary, score, keywords, content_snippet, processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data.get('title', ''),
                    article_data.get('url', ''),
                    article_data.get('source', ''),
                    article_data.get('publication_date', ''),
                    article_data.get('discovery_date', ''),
                    article_data.get('summary', ''),
                    article_data.get('score', 0.0),
                    article_data.get('keywords', ''),
                    article_data.get('content_snippet', ''),
                    article_data.get('processed', False)
                ))
                
                conn.commit()
                logger.info(f"Added new article: {article_data['title']}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding article: {e}")
            return False
    
    def update_article(self, article_id, update_data):
        """Update an existing article in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert keywords list to JSON string if it's a list
                if 'keywords' in update_data and isinstance(update_data['keywords'], list):
                    update_data['keywords'] = json.dumps(update_data['keywords'])
                
                # Build SET clause dynamically based on update_data
                set_clauses = []
                values = []
                
                for key, value in update_data.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                # Add article_id to values
                values.append(article_id)
                
                # Execute the update
                cursor.execute(f'''
                UPDATE articles SET {", ".join(set_clauses)} WHERE id = ?
                ''', values)
                
                conn.commit()
                logger.info(f"Updated article ID {article_id}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating article: {e}")
            return False
    
    def get_unprocessed_articles(self, limit=10):
        """Get articles that haven't been processed yet"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM articles 
                WHERE processed = FALSE
                ORDER BY discovery_date DESC
                LIMIT ?
                ''', (limit,))
                
                articles = [dict(row) for row in cursor.fetchall()]
                
                # Convert JSON keywords string back to list
                for article in articles:
                    if article['keywords'] and article['keywords'].startswith('['):
                        try:
                            article['keywords'] = json.loads(article['keywords'])
                        except:
                            pass
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting unprocessed articles: {e}")
            return []
    
    def get_recent_articles(self, limit=20):
        """Get the most recently processed articles"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM articles 
                WHERE processed = TRUE
                ORDER BY discovery_date DESC
                LIMIT ?
                ''', (limit,))
                
                articles = [dict(row) for row in cursor.fetchall()]
                
                # Convert JSON keywords string back to list
                for article in articles:
                    if article['keywords'] and article['keywords'].startswith('['):
                        try:
                            article['keywords'] = json.loads(article['keywords'])
                        except:
                            pass
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []
    
    def search_articles(self, query, limit=20):
        """Search articles by title, summary, or keywords"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM articles 
                WHERE processed = TRUE
                AND (
                    title LIKE ? 
                    OR summary LIKE ? 
                    OR keywords LIKE ?
                )
                ORDER BY score DESC
                LIMIT ?
                ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
                
                articles = [dict(row) for row in cursor.fetchall()]
                
                # Convert JSON keywords string back to list
                for article in articles:
                    if article['keywords'] and article['keywords'].startswith('['):
                        try:
                            article['keywords'] = json.loads(article['keywords'])
                        except:
                            pass
                
                return articles
                
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []
    
    def update_statistics(self):
        """Update the statistics table with current data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                today = datetime.now().date().isoformat()
                
                # Get statistics for today
                cursor.execute('''
                SELECT COUNT(*) as articles_found
                FROM articles 
                WHERE DATE(discovery_date) = ?
                ''', (today,))
                articles_found = cursor.fetchone()[0]
                
                cursor.execute('''
                SELECT COUNT(*) as articles_processed
                FROM articles 
                WHERE DATE(discovery_date) = ?
                AND processed = TRUE
                ''', (today,))
                articles_processed = cursor.fetchone()[0]
                
                cursor.execute('''
                SELECT AVG(score) as avg_score
                FROM articles 
                WHERE DATE(discovery_date) = ?
                AND processed = TRUE
                ''', (today,))
                avg_score = cursor.fetchone()[0] or 0.0
                
                # Get top keywords (this is simplified)
                cursor.execute('''
                SELECT keywords
                FROM articles 
                WHERE DATE(discovery_date) = ?
                AND processed = TRUE
                ''', (today,))
                
                all_keywords = []
                for row in cursor.fetchall():
                    if row[0] and row[0].startswith('['):
                        try:
                            keywords = json.loads(row[0])
                            all_keywords.extend(keywords)
                        except:
                            pass
                
                # Count keyword frequency and get top 5
                keyword_counts = {}
                for keyword in all_keywords:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                top_keywords_json = json.dumps([k for k, v in top_keywords])
                
                # Check if stats for today already exist
                cursor.execute('''
                SELECT id FROM statistics
                WHERE date = ?
                ''', (today,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing stats
                    cursor.execute('''
                    UPDATE statistics SET
                    articles_found = ?,
                    articles_processed = ?,
                    avg_score = ?,
                    top_keywords = ?
                    WHERE date = ?
                    ''', (articles_found, articles_processed, avg_score, top_keywords_json, today))
                else:
                    # Insert new stats
                    cursor.execute('''
                    INSERT INTO statistics (
                        date, articles_found, articles_processed, avg_score, top_keywords
                    ) VALUES (?, ?, ?, ?, ?)
                    ''', (today, articles_found, articles_processed, avg_score, top_keywords_json))
                
                conn.commit()
                logger.info(f"Updated statistics for {today}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False
    
    def get_statistics(self, days=7):
        """Get recent statistics"""
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT *
                FROM statistics
                ORDER BY date DESC
                LIMIT ?
                ''', (days,))
                
                stats = [dict(row) for row in cursor.fetchall()]
                
                # Convert JSON top_keywords string back to list
                for stat in stats:
                    if stat['top_keywords'] and stat['top_keywords'].startswith('['):
                        try:
                            stat['top_keywords'] = json.loads(stat['top_keywords'])
                        except:
                            pass
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return []
