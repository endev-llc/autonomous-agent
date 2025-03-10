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
from web_server import WebServer

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

    # Initialize the state monitor
    state_monitor = StateMonitor()
    logger.info("State monitor initialized")
    
    # Initialize and start the web server
    web_server = WebServer(agent)
    agent.model.set_web_server(web_server)
    web_server.start()
    logger.info("Web server started")
    
    # Schedule regular actions
    schedule.every(config["agent"]["action_interval"]).hours.do(agent.run_action_cycle)
    
    # Schedule reflection
    schedule.every(config["agent"]["reflection_interval"]).hours.do(agent.run_reflection)
    

    
    # Initial action to start the process
    agent.run_action_cycle()
    
    # Log the startup
    web_server.log_interaction('info', f'Agent "{agent.name}" initialized with goal: {agent.goal}')
    web_server.log_interaction('info', f'Using model: {agent.model.model_id}')
    
    # Main loop
    logger.info("Agent is running. Web dashboard available at http://localhost:3000")
    logger.info("Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        web_server.log_interaction('info', 'Agent stopped by user')
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        web_server.log_interaction('error', f'Error in main loop: {str(e)}')
        raise

if __name__ == "__main__":
    main()