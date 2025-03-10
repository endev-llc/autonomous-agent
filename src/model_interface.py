"""
Handles interaction with the language model API.
"""
import os
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
