import os
import threading
import time
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import after loading environment variables
from agent import PhysicsArticleCurator
from web_server import run_server

def start_web_server():
    """Start the web server in a separate thread"""
    logger.info("Starting web server thread")
    
    # Determine if we're in development mode
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    
    # Run the web server
    run_server(host='0.0.0.0', port=5000, debug=debug_mode)

def start_agent(run_once=False):
    """Start the agent in the main thread"""
    logger.info("Starting physics article curator agent")
    
    # Create and configure the agent
    agent = PhysicsArticleCurator()
    
    # Run the agent once or continuously
    if run_once:
        agent.run_once()
    else:
        agent.run_forever()

def main():
    """Main entry point for the application"""
    logger.info("Starting the Physics Article Curator application")
    
    # Check if the OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        print("Error: OPENAI_API_KEY environment variable is required but not set")
        return
    
    # Start the web server in a separate thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Give the web server a moment to start
    time.sleep(2)
    
    # Check for special run modes
    run_once = os.environ.get("RUN_ONCE", "false").lower() == "true"
    web_only = os.environ.get("WEB_ONLY", "false").lower() == "true"
    
    if web_only:
        logger.info("Running in web-only mode (no agent)")
        # Keep the main thread alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
    else:
        # Start the agent in the main thread
        start_agent(run_once=run_once)

if __name__ == "__main__":
    main()
