"""
Utility functions for the agent.
"""
import os
import sys
from loguru import logger

def show_agent_state():
    """Show the current state of the agent."""
    from state_monitor import StateMonitor
    monitor = StateMonitor()
    monitor.print_status_report()

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logger
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(sys.stderr, level="INFO")
    
    # Add file handler
    log_file = os.path.join(log_dir, "agent_{time}.log")
    logger.add(log_file, rotation="1 day", retention="7 days", level="DEBUG")
    
    logger.info("Logging initialized")