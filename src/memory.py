"""
Memory module for managing the agent's memory.
"""
import os
from datetime import datetime
from loguru import logger

class Memory:
    """
    Manages the agent's external memory storage.
    """
    def __init__(self, config):
        """Initialize memory with configuration."""
        self.config = config
        self.memory_file = "data/memory.txt"
        self.max_tokens = config.get("max_tokens", 16000)
        self.structure = config.get("structure", [])
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
    
    def exists(self):
        """Check if the memory file exists."""
        return os.path.exists(self.memory_file) and os.path.getsize(self.memory_file) > 0
    
    def read(self):
        """Read the memory file."""
        try:
            if not self.exists():
                return ""
            
            with open(self.memory_file, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            return ""
    
    def write(self, content):
        """Write content to the memory file."""
        try:
            with open(self.memory_file, "w") as f:
                f.write(content)
            logger.debug("Memory updated")
            return True
        except Exception as e:
            logger.error(f"Error writing memory: {e}")
            return False
    
    def update_with_action(self, action_result):
        """Update memory with the result of an action."""
        try:
            memory_content = self.read()
            
            # Add action result with timestamp
            updated_content = f"{memory_content}\n\n## Action Taken at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{action_result}\n"
            
            # Simple token management (approximation)
            if len(updated_content) > self.max_tokens * 4:  # Rough approximation
                half_keep = self.max_tokens * 2
                updated_content = updated_content[:half_keep] + "\n\n[...Memory truncated...]\n\n" + updated_content[-half_keep:]
            
            return self.write(updated_content)
        except Exception as e:
            logger.error(f"Error updating memory with action: {e}")
            return False
    
    def update_with_reflection(self, reflection_result):
        """Update memory with the result of a reflection."""
        try:
            current_memory = self.read()
            
            # Add reflection with timestamp
            reflection_header = f"\n\n## Reflection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            updated_content = current_memory + reflection_header + reflection_result
            
            # Manage token limit
            if len(updated_content) > self.max_tokens * 4:
                half_keep = self.max_tokens * 2
                updated_content = updated_content[:half_keep] + "\n\n[...Memory truncated...]\n\n" + updated_content[-half_keep:]
            
            return self.write(updated_content)
        except Exception as e:
            logger.error(f"Error updating memory with reflection: {e}")
            return False