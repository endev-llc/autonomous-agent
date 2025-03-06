"""
Utilities for monitoring and managing the agent's state.
"""
import os
import json
from datetime import datetime
from loguru import logger

class StateMonitor:
    """Monitors and manages the agent's state."""
    
    def __init__(self):
        """Initialize the state monitor."""
        self.data_dir = "data"
        self.model_state_path = os.path.join(self.data_dir, "model_state.json")
        self.fine_tuning_data_path = os.path.join(self.data_dir, "fine_tuning_data.jsonl")
        self.memory_path = os.path.join(self.data_dir, "memory.txt")
        
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_model_state(self):
        """Get the current model state."""
        if os.path.exists(self.model_state_path):
            try:
                with open(self.model_state_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading model state: {e}")
        
        return None
    
    def get_fine_tuning_stats(self):
        """Get statistics about fine-tuning data."""
        if not os.path.exists(self.fine_tuning_data_path):
            return {"examples_count": 0, "exists": False}
        
        try:
            examples_count = 0
            with open(self.fine_tuning_data_path, "r") as f:
                for line in f:
                    if line.strip():
                        examples_count += 1
            
            stats = {
                "examples_count": examples_count,
                "exists": True,
                "file_size_bytes": os.path.getsize(self.fine_tuning_data_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(self.fine_tuning_data_path)).isoformat()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting fine-tuning stats: {e}")
            return {"examples_count": 0, "exists": False, "error": str(e)}
    
    def get_memory_stats(self):
        """Get statistics about memory file."""
        if not os.path.exists(self.memory_path):
            return {"exists": False}
        
        try:
            with open(self.memory_path, "r") as f:
                memory_content = f.read()
            
            stats = {
                "exists": True,
                "file_size_bytes": os.path.getsize(self.memory_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(self.memory_path)).isoformat(),
                "characters": len(memory_content),
                "lines": len(memory_content.splitlines())
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"exists": False, "error": str(e)}
    
    def get_agent_status(self):
        """Get the overall status of the agent."""
        model_state = self.get_model_state()
        fine_tuning_stats = self.get_fine_tuning_stats()
        memory_stats = self.get_memory_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "model_state": model_state,
            "fine_tuning_stats": fine_tuning_stats,
            "memory_stats": memory_stats
        }
    
    def print_status_report(self):
        """Print a human-readable status report."""
        status = self.get_agent_status()
        
        print("\n=== AGENT STATUS REPORT ===")
        print(f"Time: {status['timestamp']}")
        
        # Model State
        model_state = status.get("model_state")
        if model_state:
            print("\n--- MODEL STATE ---")
            print(f"Base Model: {model_state.get('base_model_id', 'Not set')}")
            print(f"Fine-tuned Model: {model_state.get('fine_tuned_model_id', 'None')}")
            print(f"Active Fine-tuning Job: {model_state.get('active_fine_tuning_job', 'None')}")
            
            history = model_state.get("fine_tuning_history", [])
            if history:
                print(f"\nFine-tuning History ({len(history)} jobs):")
                for i, job in enumerate(history[-3:], 1):  # Show last 3 jobs
                    print(f"  {i}. Job {job.get('job_id')}: {job.get('status')} (Model: {job.get('starting_model')})")
                
                if len(history) > 3:
                    print(f"  ... and {len(history) - 3} more job(s)")
        else:
            print("\n--- MODEL STATE ---")
            print("No model state found")
        
        # Fine-tuning Stats
        ft_stats = status.get("fine_tuning_stats", {})
        print("\n--- FINE-TUNING DATA ---")
        print(f"Examples: {ft_stats.get('examples_count', 0)}")
        if ft_stats.get("exists"):
            print(f"Last Modified: {ft_stats.get('last_modified', 'Unknown')}")
            size_kb = ft_stats.get("file_size_bytes", 0) / 1024
            print(f"File Size: {size_kb:.2f} KB")
        
        # Memory Stats
        mem_stats = status.get("memory_stats", {})
        print("\n--- MEMORY ---")
        if mem_stats.get("exists"):
            print(f"Lines: {mem_stats.get('lines', 0)}")
            print(f"Characters: {mem_stats.get('characters', 0)}")
            print(f"Last Modified: {mem_stats.get('last_modified', 'Unknown')}")
            size_kb = mem_stats.get("file_size_bytes", 0) / 1024
            print(f"File Size: {size_kb:.2f} KB")
        else:
            print("Memory file not found")
        
        print("\n===========================\n")