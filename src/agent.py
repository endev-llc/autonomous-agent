import os
import time
import json
import yaml
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple
import openai
from loguru import logger
from database import ArticleDatabase

class PhysicsArticleCurator:
    def __init__(self, config_path="config.yaml"):
        """Initialize the agent with configuration"""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize database
        self.db = ArticleDatabase()
        
        # Initialize OpenAI client
        self._setup_openai()
        
        # Agent state
        self.name = self.config["agent"]["name"]
        self.goal = self.config["agent"]["goal"]
        self.action_interval = self.config["agent"]["action_interval"] * 3600  # convert to seconds
        
        # Agent memory
        self.memory = {
            "Agent Identity and Goal": self._format_identity(),
            "Recent Articles": [],
            "Search Topics": self._get_initial_search_topics(),
            "Statistics": {}
        }
        
        logger.info(f"Agent '{self.name}' initialized with goal: {self.goal}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config
            return {
                "agent": {
                    "name": "PhysicsArticleCurator",
                    "goal": "Find and analyze physics articles",
                    "action_interval": 6  # hours
                },
                "model": {
                    "provider": "openai",
                    "model_id": "gpt-4o-search-preview",
                    "web_search_enabled": True,
                    "max_search_tokens": 4000,
                    "max_analysis_tokens": 2000
                },
                "memory": {
                    "max_tokens": 4000,
                    "structure": [
                        "Agent Identity and Goal",
                        "Recent Articles",
                        "Search Topics",
                        "Statistics"
                    ]
                }
            }
    
    def _setup_logging(self):
        """Configure logging"""
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/agent_{datetime.now().strftime('%Y%m%d')}.log"
        logger.add(log_file, rotation="1 day", retention="7 days", level="INFO")
    
    def _setup_openai(self):
        """Initialize OpenAI client"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized")
        
        # Test if the client can access the responses API
        try:
            # Make a simple call to test connectivity
            test_response = self.client.responses.create(
                model="gpt-4o",
                input="Hello"
            )
            logger.info("OpenAI responses API test successful")
            self.use_responses_api = True
        except Exception as e:
            logger.error(f"Error testing OpenAI responses API: {e}")
            logger.warning("Falling back to chat completions API")
            self.use_responses_api = False
    
    def _format_identity(self) -> str:
        """Format agent identity for memory"""
        return f"I am {self.name}, an autonomous agent. My goal is: {self.goal}"
    
    def _get_initial_search_topics(self) -> List[str]:
        """Get initial search topics for physics articles"""
        return [
            "latest quantum physics research",
            "recent physics breakthroughs",
            "new physics papers in Nature journal",
            "particle physics research updates",
            "astrophysics discoveries",
            "condensed matter physics news",
            "string theory developments",
            "theoretical physics advancements",
            "experimental physics results"
        ]
    
    def _format_memory(self) -> str:
        """Format agent memory for prompt"""
        memory_text = ""
        max_tokens = self.config["memory"]["max_tokens"]
        
        # Add each memory section
        for section in self.config["memory"]["structure"]:
            if section in self.memory:
                content = self.memory[section]
                if isinstance(content, list):
                    content = "\n- " + "\n- ".join(content)
                elif isinstance(content, dict):
                    content = "\n- " + "\n- ".join([f"{k}: {v}" for k, v in content.items()])
                
                memory_text += f"## {section}\n{content}\n\n"
        
        # Simple truncation - in practice, you'd want a more sophisticated approach
        if len(memory_text) > max_tokens:
            memory_text = memory_text[:max_tokens] + "..."
        
        return memory_text
    
    def run_forever(self):
        """Run the agent continuously"""
        logger.info(f"Starting {self.name} agent loop")
        
        while True:
            try:
                # Run one cycle of the agent
                self.run_once()
                
                # Update statistics
                self.db.update_statistics()
                
                # Update memory with recent statistics
                stats = self.db.get_statistics(days=1)
                if stats:
                    self.memory["Statistics"] = {
                        "Articles Found Today": stats[0].get("articles_found", 0),
                        "Articles Processed Today": stats[0].get("articles_processed", 0),
                        "Average Score": round(stats[0].get("avg_score", 0), 2),
                        "Top Keywords": ", ".join(stats[0].get("top_keywords", []))
                    }
                
                # Sleep until next cycle
                logger.info(f"Sleeping for {self.action_interval} seconds")
                time.sleep(self.action_interval)
                
            except KeyboardInterrupt:
                logger.info("Agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                # Sleep for a while before retrying
                time.sleep(60)
    
    def run_once(self):
        """Run one cycle of the agent's operations"""
        logger.info("Starting agent cycle")
        
        # Step 1: Find new physics articles
        articles = self.find_physics_articles()
        
        # Step 2: Process and analyze unprocessed articles
        processed_count = self.process_articles()
        
        # Step 3: Reflect and update search topics
        self.reflect_and_update_topics()
        
        logger.info(f"Completed agent cycle. Found {len(articles)} new articles, processed {processed_count}.")
    
    def find_physics_articles(self) -> List[Dict[str, Any]]:
        """Search for and find new physics articles"""
        logger.info("Searching for new physics articles")
        
        # Use search topics to find articles
        search_topics = self.memory["Search Topics"]
        
        # Randomly select 2-3 topics to search for this cycle
        topics_to_search = random.sample(search_topics, min(3, len(search_topics)))
        
        all_articles = []
        for topic in topics_to_search:
            try:
                articles = self._search_for_articles(topic)
                all_articles.extend(articles)
                
                # Add articles to database
                for article in articles:
                    self.db.add_article(article)
                
                logger.info(f"Found {len(articles)} articles for topic: {topic}")
            except Exception as e:
                logger.error(f"Error searching for topic '{topic}': {e}")
        
        # Update memory with most recent articles
        if all_articles:
            self.memory["Recent Articles"] = [
                f"{a['title']} ({a['source']})" for a in all_articles[:5]
            ]
        
        return all_articles
    
    def _search_for_articles(self, topic: str) -> List[Dict[str, Any]]:
        """Search for articles on a specific topic using the OpenAI web search"""
        logger.info(f"Searching for articles on topic: {topic}")
        
        # Construct a search prompt
        prompt = f"""
        You're a physics research assistant looking for the latest physics articles and research papers.
        Search for recent, high-quality physics articles on: {topic}
        
        For each article found, extract the following details in a structured format:
        - Title
        - URL
        - Source/Publication
        - Publication date (if available)
        - A brief snippet of the content
        
        ONLY return articles that are related to physics research or news.
        Format your findings as a JSON array of objects.
        """
        
        try:
            # Try new Responses API first
            if hasattr(self, 'use_responses_api') and self.use_responses_api:
                try:
                    response = self.client.responses.create(
                        model=self.config["model"]["model_id"],
                        tools=[{"type": "web_search_preview"}],
                        tool_choice={"type": "web_search_preview"},
                        input=prompt
                    )
                    content = response.output_text
                    logger.info("Successfully used responses API for search")
                except Exception as e:
                    logger.error(f"Error with responses API: {e}")
                    content = None
            else:
                content = None
                
            # Fall back to chat completions API if needed
            if content is None:
                response = self.client.chat.completions.create(
                    model=self.config["model"]["model_id"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=self.config["model"]["max_search_tokens"],
                )
                content = response.choices[0].message.content
                logger.info("Used chat completions API for search")
            
            # Extract JSON from the response (handling potential text around the JSON)
            articles = self._extract_json_from_response(content)
            
            # Add discovery date
            for article in articles:
                article["discovery_date"] = datetime.now().isoformat()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []
    
    def _extract_json_from_response(self, content: str) -> List[Dict[str, Any]]:
        """Extract JSON array from response text which may have additional text"""
        try:
            # Try to parse the entire response as JSON
            return json.loads(content)
        except:
            # If that fails, try to find the JSON array in the text
            try:
                # Look for JSON array pattern
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    logger.warning("Could not find JSON array in response")
                    return []
            except Exception as e:
                logger.error(f"Error extracting JSON from response: {e}")
                return []
    
    def process_articles(self) -> int:
        """Process unanalyzed articles in the database"""
        # Get unprocessed articles
        articles = self.db.get_unprocessed_articles(limit=5)
        logger.info(f"Processing {len(articles)} unprocessed articles")
        
        processed_count = 0
        for article in articles:
            try:
                # Analyze the article
                result = self._analyze_article(article)
                
                # Update the article in the database
                self.db.update_article(article["id"], {
                    "summary": result["summary"],
                    "keywords": result["keywords"],
                    "score": result["score"],
                    "processed": True
                })
                
                processed_count += 1
                logger.info(f"Processed article: {article['title']}")
                
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {e}")
        
        return processed_count
    
    def _analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a physics article for summary, keywords, and score"""
        logger.info(f"Analyzing article: {article['title']}")
        
        # Construct a prompt for analysis
        prompt = f"""
        Below is information about a physics article. Please analyze it and provide:
        1. A concise summary (3-5 sentences)
        2. Exactly 3 keywords that best categorize this article
        3. A significance score from 1.0 to 10.0 where:
           - 1.0-3.9: Minor update or news with limited importance
           - 4.0-6.9: Interesting development with moderate significance
           - 7.0-8.9: Important discovery or advancement
           - 9.0-10.0: Groundbreaking, field-changing research
        
        Article Title: {article.get('title', 'Unknown')}
        Source: {article.get('source', 'Unknown')}
        Publication Date: {article.get('publication_date', 'Unknown')}
        Content Snippet: {article.get('content_snippet', '')}
        URL: {article.get('url', '')}
        
        Return your analysis in JSON format with keys: "summary", "keywords" (as array of exactly 3 strings), and "score" (as a float).
        """
        
        try:
            # Get content from API
            content = None
            if hasattr(self, 'use_responses_api') and self.use_responses_api:
                # Use responses API
                try:
                    response = self.client.responses.create(
                        model=self.config["model"]["model_id"],
                        input=prompt
                    )
                    content = response.output_text
                except Exception as api_error:
                    logger.error(f"Error with responses API: {api_error}")
                    content = None
            
            # Fall back to chat completions if needed
            if content is None:
                response = self.client.chat.completions.create(
                    model=self.config["model"]["model_id"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=self.config["model"]["max_analysis_tokens"],
                )
                content = response.choices[0].message.content
            
            # Extract JSON from response
            analysis = self._extract_json_from_response(content)
            
            # If we got a list, take the first item
            if isinstance(analysis, list) and len(analysis) > 0:
                analysis = analysis[0]
            
            # Validate and clean analysis
            if not isinstance(analysis, dict):
                analysis = {}
            
            # Ensure we have all required fields
            result = {
                "summary": analysis.get("summary", "No summary available."),
                "keywords": analysis.get("keywords", ["physics", "research", "science"])[:3],
                "score": float(analysis.get("score", 5.0))
            }
            
            # Validate score range
            result["score"] = max(1.0, min(10.0, result["score"]))
            
            # Ensure we have exactly 3 keywords
            while len(result["keywords"]) < 3:
                result["keywords"].append(random.choice(["physics", "science", "research"]))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in article analysis: {e}")
            # Return default analysis
            return {
                "summary": "Failed to generate summary due to technical error.",
                "keywords": ["physics", "research", "science"],
                "score": 5.0
            }
    
    def reflect_and_update_topics(self):
        """Reflect on recent findings and update search topics"""
        logger.info("Reflecting and updating search topics")
        
        # Get recent article data
        recent_articles = self.db.get_recent_articles(limit=10)
        article_info = ""
        
        for article in recent_articles:
            article_info += f"Title: {article['title']}\n"
            article_info += f"Keywords: {', '.join(article['keywords'] if isinstance(article['keywords'], list) else [])}\n"
            article_info += f"Score: {article['score']}\n\n"
        
        # Current topics
        current_topics = self.memory["Search Topics"]
        current_topics_text = "\n".join(current_topics)
        
        # Construct a prompt for reflection
        prompt = f"""
        You are {self.name}, a physics article curator. Based on recent articles collected and your goal, suggest 5-10 search topics for finding more physics articles.

        Your goal: {self.goal}
        
        Recent articles collected:
        {article_info}
        
        Current search topics:
        {current_topics_text}
        
        Generate 5-10 specific search topics that would help find high-quality physics articles. These should be search phrases, not just keywords.
        Include a mix of:
        1. General physics news topics
        2. Specific subfields (quantum physics, astrophysics, etc.)
        3. Topics related to recent significant articles
        4. Topics about emerging physics research areas
        
        Return only the list of topics, one per line.
        """
        
        try:
            # Get content from API
            content = None
            if hasattr(self, 'use_responses_api') and self.use_responses_api:
                # Use responses API
                try:
                    response = self.client.responses.create(
                        model=self.config["model"]["model_id"],
                        input=prompt
                    )
                    content = response.output_text
                except Exception as api_error:
                    logger.error(f"Error with responses API: {api_error}")
                    content = None
            
            # Fall back to chat completions if needed
            if content is None:
                response = self.client.chat.completions.create(
                    model=self.config["model"]["model_id"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                )
                content = response.choices[0].message.content
            
            # Extract topics (one per line)
            new_topics = [
                topic.strip() for topic in content.strip().split("\n")
                if topic.strip() and not topic.startswith(("#", "-", "*", "1.", "2."))
            ]
            
            # Filter out any non-topic lines
            new_topics = [
                topic for topic in new_topics 
                if len(topic.split()) >= 2 and len(topic) < 100
            ]
            
            # Update search topics if we have enough
            if len(new_topics) >= 5:
                self.memory["Search Topics"] = new_topics
                logger.info(f"Updated search topics: {len(new_topics)} new topics")
            else:
                logger.warning(f"Not enough new topics generated ({len(new_topics)}), keeping current topics")
            
        except Exception as e:
            logger.error(f"Error in reflection: {e}")


if __name__ == "__main__":
    # This allows for testing the agent directly
    agent = PhysicsArticleCurator()
    agent.run_once()
