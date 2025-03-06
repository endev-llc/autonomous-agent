"""
Handles interaction with the language model API,
including queries and fine-tuning.
"""
import os
import json
import jsonlines
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
        self.fine_tuning_config = config.get("fine_tuning", {})
        self.fine_tuning_enabled = self.fine_tuning_config.get("enabled", False)
        
        # Set up API client
        if self.provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            raise ValueError(f"Unsupported model provider: {self.provider}")
        
        # Fine-tuning data path
        self.fine_tuning_data_path = "data/fine_tuning_data.jsonl"
        self.examples_to_keep = self.fine_tuning_config.get("examples_to_keep", 100)
        
        # Initialize or load fine-tuning data file
        os.makedirs(os.path.dirname(self.fine_tuning_data_path), exist_ok=True)
        if not os.path.exists(self.fine_tuning_data_path):
            with open(self.fine_tuning_data_path, "w") as f:
                pass  # Create empty file
    
    def query(self, prompt, max_tokens=2000):
        """Query the language model API."""
        try:
            if self.provider == "openai":
                response = openai.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "system", "content": prompt}],
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                
                # Save the interaction for potential fine-tuning
                if self.fine_tuning_enabled:
                    self._save_interaction_for_fine_tuning(prompt, content)
                
                return content
        except Exception as e:
            logger.error(f"Error querying model: {e}")
            return f"Error: Unable to get a response from the model. {str(e)}"
    
    def _save_interaction_for_fine_tuning(self, prompt, response):
        """Save the interaction for future fine-tuning."""
        try:
            # Create a fine-tuning example
            example = {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "assistant", "content": response}
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            # Read existing examples
            examples = []
            try:
                with jsonlines.open(self.fine_tuning_data_path, "r") as reader:
                    for obj in reader:
                        examples.append(obj)
            except Exception:
                pass  # File might be empty or not exist
            
            # Add the new example
            examples.append(example)
            
            # Keep only the most recent examples
            examples = examples[-self.examples_to_keep:]
            
            # Write back the examples
            with jsonlines.open(self.fine_tuning_data_path, "w") as writer:
                for obj in examples:
                    writer.write(obj)
            
            logger.debug(f"Saved interaction for fine-tuning, total examples: {len(examples)}")
        except Exception as e:
            logger.error(f"Error saving interaction for fine-tuning: {e}")
    
    def has_enough_fine_tuning_data(self, min_examples=10):
        """Check if we have enough data for fine-tuning."""
        try:
            count = 0
            with jsonlines.open(self.fine_tuning_data_path, "r") as reader:
                for _ in reader:
                    count += 1
            return count >= min_examples
        except Exception as e:
            logger.error(f"Error checking fine-tuning data: {e}")
            return False
    
    def run_fine_tuning(self):
        """Run the fine-tuning process."""
        if not self.fine_tuning_enabled:
            logger.warning("Fine-tuning is disabled in the configuration")
            return False
        
        if not self.has_enough_fine_tuning_data():
            logger.warning("Not enough data for fine-tuning")
            return False
        
        try:
            # Create a fine-tuning file
            logger.info("Creating fine-tuning file")
            with open(self.fine_tuning_data_path, "rb") as f:
                response = openai.files.create(
                    file=f,
                    purpose="fine-tune"
                )
            file_id = response.id
            logger.info(f"Fine-tuning file created: {file_id}")
            
            # Create a fine-tuning job
            logger.info("Creating fine-tuning job")
            base_model = self.fine_tuning_config.get("base_model", "gpt-4o")
            response = openai.fine_tuning.jobs.create(
                training_file=file_id,
                model=base_model,
            )
            job_id = response.id
            logger.info(f"Fine-tuning job created: {job_id}")
            
            # In a real implementation, you would poll for job status
            # For this example, we'll log that it's processing
            logger.info(f"Fine-tuning job {job_id} is processing. This can take a while...")
            
            # When the job completes, you would update the model ID:
            # self.model_id = "ft:gpt-4o-..." (from job completion)
            
            # For now, we'll consider it a success if the job was created
            return True
        except Exception as e:
            logger.error(f"Error running fine-tuning: {e}")
            return False