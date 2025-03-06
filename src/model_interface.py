"""
Handles interaction with the language model API,
including queries and fine-tuning.
"""
import os
import json
import time
import jsonlines
from datetime import datetime
from loguru import logger
import openai
import threading

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
        
        # Fine-tuning data and state paths
        self.data_dir = "data"
        self.fine_tuning_data_path = os.path.join(self.data_dir, "fine_tuning_data.jsonl")
        self.model_state_path = os.path.join(self.data_dir, "model_state.json")
        self.examples_to_keep = self.fine_tuning_config.get("examples_to_keep", 100)
        self.min_examples_for_fine_tuning = 5  # Reduced from 10 for faster testing
        
        # Make sure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize or load fine-tuning data file
        if not os.path.exists(self.fine_tuning_data_path):
            with open(self.fine_tuning_data_path, "w") as f:
                pass  # Create empty file
        
        # Load model state or create default state
        self.load_model_state()
        
        # Check for any pending fine-tuning jobs
        if self.model_state.get("active_fine_tuning_job"):
            self._check_fine_tuning_job_status()
    
    def load_model_state(self):
        """Load the model state from the state file or create default state."""
        if os.path.exists(self.model_state_path):
            try:
                with open(self.model_state_path, "r") as f:
                    self.model_state = json.load(f)
                    
                # If a fine-tuned model exists, use it
                if self.model_state.get("fine_tuned_model_id"):
                    self.model_id = self.model_state["fine_tuned_model_id"]
                    logger.info(f"Using fine-tuned model: {self.model_id}")
                
                return
            except Exception as e:
                logger.error(f"Error loading model state, using defaults: {e}")
        
        # Create default state
        self.model_state = {
            "base_model_id": self.model_id,
            "fine_tuned_model_id": None,
            "active_fine_tuning_job": None,
            "fine_tuning_history": [],
            "last_updated": datetime.now().isoformat()
        }
        self.save_model_state()
    
    def save_model_state(self):
        """Save the current model state to disk."""
        self.model_state["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.model_state_path, "w") as f:
                json.dump(self.model_state, f, indent=2)
            logger.debug("Model state saved")
        except Exception as e:
            logger.error(f"Error saving model state: {e}")
    
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
    
    def has_enough_fine_tuning_data(self):
        """Check if we have enough data for fine-tuning."""
        try:
            count = 0
            with jsonlines.open(self.fine_tuning_data_path, "r") as reader:
                for _ in reader:
                    count += 1
            return count >= self.min_examples_for_fine_tuning
        except Exception as e:
            logger.error(f"Error checking fine-tuning data: {e}")
            return False
    
    def run_fine_tuning(self):
        """Run the fine-tuning process if not already in progress."""
        if not self.fine_tuning_enabled:
            logger.warning("Fine-tuning is disabled in the configuration")
            return False
        
        # Check if a fine-tuning job is already in progress
        if self.model_state.get("active_fine_tuning_job"):
            logger.info(f"Fine-tuning job already in progress: {self.model_state['active_fine_tuning_job']}")
            # Check the status of the existing job
            self._check_fine_tuning_job_status()
            return True
        
        if not self.has_enough_fine_tuning_data():
            logger.warning(f"Not enough data for fine-tuning (minimum: {self.min_examples_for_fine_tuning})")
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
            
            # Use the base model or the most recent fine-tuned model as starting point
            starting_model = self.model_state.get("fine_tuned_model_id") or base_model
            
            response = openai.fine_tuning.jobs.create(
                training_file=file_id,
                model=starting_model,
            )
            job_id = response.id
            
            # Update model state with the new job
            self.model_state["active_fine_tuning_job"] = job_id
            self.model_state["fine_tuning_history"].append({
                "job_id": job_id,
                "file_id": file_id,
                "starting_model": starting_model,
                "status": "created",
                "created_at": datetime.now().isoformat()
            })
            self.save_model_state()
            
            logger.info(f"Fine-tuning job created: {job_id}")
            
            # Start a background thread to poll the job status
            threading.Thread(target=self._poll_fine_tuning_job, args=(job_id,), daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"Error running fine-tuning: {e}")
            return False
    
    def _poll_fine_tuning_job(self, job_id, initial_delay=60, max_retries=20, backoff_factor=1.5):
        """Poll the fine-tuning job status in a background thread."""
        time.sleep(initial_delay)  # Wait for job to initialize
        
        retry_count = 0
        retry_delay = initial_delay
        
        while retry_count < max_retries:
            try:
                status = self._check_fine_tuning_job_status()
                
                # If job completed or failed, stop polling
                if status in ["succeeded", "failed", "cancelled"]:
                    break
                
                # Exponential backoff
                retry_delay = min(retry_delay * backoff_factor, 600)  # Max 10 minutes
                retry_count += 1
                time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Error polling fine-tuning job: {e}")
                retry_count += 1
                time.sleep(retry_delay)
    
    def _check_fine_tuning_job_status(self):
        """Check the status of the active fine-tuning job."""
        job_id = self.model_state.get("active_fine_tuning_job")
        if not job_id:
            return None
        
        try:
            job = openai.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            # Update the job status in model state
            for job_info in self.model_state["fine_tuning_history"]:
                if job_info["job_id"] == job_id:
                    job_info["status"] = status
                    job_info["last_checked"] = datetime.now().isoformat()
                    break
            
            # If job completed successfully, update the model ID
            if status == "succeeded":
                fine_tuned_model = job.fine_tuned_model
                logger.info(f"Fine-tuning job {job_id} completed! New model: {fine_tuned_model}")
                
                # Update the model state
                self.model_state["fine_tuned_model_id"] = fine_tuned_model
                self.model_state["active_fine_tuning_job"] = None
                
                # Update the current model ID
                self.model_id = fine_tuned_model
            
            # If job failed or was cancelled, clear the active job
            elif status in ["failed", "cancelled"]:
                logger.warning(f"Fine-tuning job {job_id} {status}")
                self.model_state["active_fine_tuning_job"] = None
            
            self.save_model_state()
            return status
            
        except Exception as e:
            logger.error(f"Error checking fine-tuning job status: {e}")
            return None