#!/usr/bin/env python3
"""
Test script for verifying memory update functionality.
"""
import os
import yaml
from loguru import logger

from agent import Agent
from utils import setup_logging

# Setup logging
setup_logging()

def load_config():
    """Load configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    """Run a test of the memory update functionality."""
    logger.info("Starting memory update test")
    
    # Load configuration
    config = load_config()
    
    # Initialize the agent
    agent = Agent(config)
    
    # Run the memory update test
    result = agent.test_memory_update()
    
    # Print summary
    updated_sections = [section for section in result["initial"] 
                      if result["initial"][section] != result["updated"][section]]
    
    if updated_sections:
        logger.info(f"Successfully updated {len(updated_sections)} memory sections: {', '.join(updated_sections)}")
    else:
        logger.warning("No memory sections were updated. The model may not be responding in the expected format.")
    
    logger.info("Memory update test completed")

if __name__ == "__main__":
    main() 