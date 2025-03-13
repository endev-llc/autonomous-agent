"""
Handles interaction with the language model API.
"""
import os
import json
from datetime import datetime
from loguru import logger
import openai

class ModelInterface:
    """Interface for interacting with the language model."""
    
    def __init__(self, config):
        """Initialize the model interface with configuration."""
        self.config = config
        self.provider = config["provider"]
        self.model_id = config["model_id"]
        self.web_server = None  # Will be set by the main.py
        
        # Set up API client
        if self.provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            raise ValueError(f"Unsupported model provider: {self.provider}")
        
        # Make sure data directory exists
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Make sure findings directory exists
        self.findings_dir = os.path.join(self.data_dir, "findings")
        os.makedirs(self.findings_dir, exist_ok=True)
        
        # Make sure connections directory exists
        self.connections_dir = os.path.join(self.data_dir, "connections")
        os.makedirs(self.connections_dir, exist_ok=True)
        
        logger.info(f"Model interface initialized with model: {self.model_id}")
        
    def set_web_server(self, web_server):
        """Set the web server reference for logging."""
        self.web_server = web_server
    
    def query(self, prompt, max_tokens=2000):
        """Query the language model API."""
        try:
            # Log the prompt if web server is available
            if self.web_server:
                self.web_server.log_prompt(prompt)
            
            start_time = datetime.now()
            
            if self.provider == "openai":
                # Log that we're sending a request
                logger.debug(f"Sending request to {self.model_id}")
                
                response = openai.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                
                # Log the response if web server is available
                if self.web_server:
                    self.web_server.log_response(content)
                    
                # Log processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Model query processed in {processing_time:.2f} seconds")
                
                return content
        except Exception as e:
            error_msg = f"Error: Unable to get a response from the model. {str(e)}"
            logger.error(f"Error querying model: {e}")
            
            # Log the error if web server is available
            if self.web_server:
                self.web_server.log_interaction('error', error_msg)
                
            return error_msg
                
    def web_search(self, query):
        """Perform a web search using OpenAI's search functionality."""
        try:
            # Log that we're performing a search
            logger.info(f"Performing web search for: {query}")
            
            # Log the search query if web server is available
            if self.web_server:
                self.web_server.log_interaction('search', f"Searching the web for: {query}")
            
            start_time = datetime.now()
            
            # Use OpenAI's API to perform the search
            response = openai.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": query}
                ],
                tools=[{
                    "type": "web_search",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information."
                    }
                }],
                tool_choice={"type": "web_search"}
            )
            
            # Process the search results
            tool_calls = response.choices[0].message.tool_calls
            
            if tool_calls:
                # Extract search results from the tool call
                search_results = json.loads(tool_calls[0].function.arguments)
                
                # Log the search results
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Web search processed in {processing_time:.2f} seconds")
                
                # Log search results if web server is available
                if self.web_server:
                    self.web_server.log_interaction('search_result', f"Search results received for: {query}")
                
                # Save search results to file
                self._save_search_results(query, search_results)
                
                # Return the search results
                return search_results
            else:
                logger.warning("No search results returned from API")
                return {"message": "No search results found"}
                
        except Exception as e:
            error_msg = f"Error: Unable to perform web search. {str(e)}"
            logger.error(f"Error performing web search: {e}")
            
            # Log the error if web server is available
            if self.web_server:
                self.web_server.log_interaction('error', error_msg)
                
            return {"error": error_msg}

    def _save_search_results(self, query, results):
        """Save search results to a file."""
        try:
            # Create a filename based on the query and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_slug = query.lower().replace(' ', '_')[:30]  # Create a slug from the query
            filename = f"{timestamp}_{query_slug}.json"
            filepath = os.path.join(self.data_dir, "search_results", filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write results to file
            with open(filepath, 'w') as f:
                json.dump({
                    "query": query,
                    "timestamp": timestamp,
                    "results": results
                }, f, indent=2)
                
            logger.debug(f"Search results saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving search results: {e}")
            return None
            
    def analyze_search_results(self, query, search_results):
        """Analyze search results using the model."""
        try:
            # Prepare a prompt for analyzing the search results
            prompt = f"""# Web Search Analysis

## Search Query
{query}

## Search Results
{json.dumps(search_results, indent=2)}

## Task
Please analyze these search results and provide:
1. A concise summary of the key information found
2. How this information relates to the goal of discovering a new law of physics
3. Any specific insights or patterns that might be worth further investigation
4. Suggestions for follow-up searches or research directions

Your analysis should be detailed but focused on the most relevant aspects for theoretical physics advancement.
"""
            
            # Get analysis from the model
            analysis = self.query(prompt, max_tokens=2000)
            
            # Log the analysis
            logger.info(f"Completed analysis of search results for: {query}")
            
            # Log analysis if web server is available
            if self.web_server:
                self.web_server.log_interaction('analysis', f"Completed analysis of search results for: {query}")
            
            # Save the analysis to a file
            self._save_analysis(query, analysis)
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error: Unable to analyze search results. {str(e)}"
            logger.error(f"Error analyzing search results: {e}")
            
            # Log the error if web server is available
            if self.web_server:
                self.web_server.log_interaction('error', error_msg)
                
            return error_msg
    
    def _save_analysis(self, query, analysis):
        """Save analysis results to a file."""
        try:
            # Create a filename based on the query and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_slug = query.lower().replace(' ', '_')[:30]  # Create a slug from the query
            filename = f"{timestamp}_{query_slug}_analysis.md"
            filepath = os.path.join(self.data_dir, "analyses", filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Format the content
            formatted_analysis = f"""# Analysis of Web Search: "{query}"
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

{analysis}
"""
            
            # Write analysis to file
            with open(filepath, 'w') as f:
                f.write(formatted_analysis)
                
            logger.debug(f"Analysis saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None

    def record_connection(self, title, content):
        """Record a connection between ideas or concepts."""
        try:
            # Create a filename based on the title and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            title_slug = title.lower().replace(' ', '_')[:30]  # Create a slug from the title
            filename = f"{timestamp}_{title_slug}.md"
            filepath = os.path.join(self.connections_dir, filename)
            
            # Format the content
            formatted_content = f"""# Connection: {title}
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

{content}
"""
            
            # Write connection to file
            with open(filepath, 'w') as f:
                f.write(formatted_content)
                
            logger.info(f"Connection recorded: {title}")
            logger.debug(f"Connection saved to {filepath}")
            
            # Log if web server is available
            if self.web_server:
                self.web_server.log_interaction('connection', f"New connection recorded: {title}")
                
            return filepath
        except Exception as e:
            logger.error(f"Error recording connection: {e}")
            return None
