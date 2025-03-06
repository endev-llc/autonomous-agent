#!/usr/bin/env python3
"""
Main entry point for the autonomous agent.
"""
import os
import time
import schedule
import yaml
from loguru import logger
from dotenv import load_dotenv

from agent import Agent
from utils import setup_logging
from state_monitor import StateMonitor

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()

def load_config():
    """Load configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    """Main function to run the autonomous agent."""
    logger.info("Starting autonomous agent")
    
    # Load configuration
    config = load_config()
    
    # Override configuration with environment variables if present
    if "AGENT_GOAL" in os.environ:
        config["agent"]["goal"] = os.environ["AGENT_GOAL"]
    
    # Initialize the agent
    agent = Agent(config)

    # Inside the main function, after initializing the agent:
    state_monitor = StateMonitor()
    logger.info("State monitor initialized")
    
    # Schedule regular actions
    schedule.every(config["agent"]["action_interval"]).hours.do(agent.run_action_cycle)
    
    # Schedule reflection
    schedule.every(config["agent"]["reflection_interval"]).hours.do(agent.run_reflection)
    
    # Schedule fine-tuning if enabled
    if config["model"]["fine_tuning"]["enabled"]:
        fine_tuning_interval = config["model"]["fine_tuning"]["interval"]
        schedule.every(fine_tuning_interval).hours.do(agent.run_fine_tuning)
    
    # Initial action to start the process
    agent.run_action_cycle()
    
    # Main loop
    logger.info("Agent is running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        raise

if __name__ == "__main__":
    main()