"""
Utilities for monitoring and managing the agent's state.
"""
import os
from datetime import datetime
from loguru import logger

class StateMonitor:
    """Monitors and manages the agent's state."""
    
    def __init__(self):
        """Initialize the state monitor."""
        self.data_dir = "data"
        self.memory_path = os.path.join(self.data_dir, "memory.txt")
        
        os.makedirs(self.data_dir, exist_ok=True)
    
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
        memory_stats = self.get_memory_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": memory_stats
        }
    
    def print_status_report(self):
        """Print a human-readable status report."""
        status = self.get_agent_status()
        
        print("\n=== AGENT STATUS REPORT ===")
        print(f"Time: {status['timestamp']}")
        
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