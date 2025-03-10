"""
Agent module that coordinates the agent's operations.
"""
import os
from datetime import datetime
from loguru import logger

from model_interface import ModelInterface
from memory import Memory
from reflection import Reflection

class Agent:
    """
    Main agent class that orchestrates the agent's operations.
    """
    def __init__(self, config):
        """Initialize the agent with configuration."""
        self.config = config
        self.name = config["agent"]["name"]
        self.goal = config["agent"]["goal"]
        
        # Initialize components
        self.memory = Memory(config["memory"])
        self.model = ModelInterface(config["model"])
        self.reflection = Reflection(self)
        
        # Initialize memory if it doesn't exist
        if not self.memory.exists():
            self.initialize_memory()
            
        logger.info(f"Agent '{self.name}' initialized with goal: {self.goal}")
    
    def initialize_memory(self):
        """Initialize the agent's memory."""
        initial_memory = f"""
# {self.name} - Autonomous Agent Memory

## Agent Identity and Goal
- Name: {self.name}
- Goal: {self.goal}
- Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Progress Summary
I am just beginning my journey. I have not yet taken any actions toward my goal.

## Recent Actions and Outcomes
No actions taken yet.

## Next Steps and Planning
1. Perform initial assessment of my capabilities
2. Develop strategy to accomplish my goal
3. Begin executing on the first steps of my plan

## Insights and Learnings
None yet. I'm eager to learn and grow as I work toward my goal.
"""
        self.memory.write(initial_memory)
        logger.info("Agent memory initialized")
    
    def run_action_cycle(self):
        """Run a single action cycle."""
        logger.info("Running action cycle")
        
        # Read memory
        memory_content = self.memory.read()
        
        # Prepare prompt for the model
        prompt = self._build_action_prompt(memory_content)
        
        # Get response from the model
        response = self.model.query(prompt)
        
        # Update memory with the response
        self.memory.update_with_action(response)
        
        # Log action
        logger.info(f"Action completed, memory updated")
        
        # Log to web interface if model has web server
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('action', 'Action cycle completed and memory updated')
            
        return response
    
    def run_reflection(self):
        """Run a reflection cycle to assess progress and update strategy."""
        logger.info("Running reflection cycle")
        reflection_result = self.reflection.perform_reflection()
        logger.info("Reflection completed")
        
        # Log to web interface if model has web server
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('reflection', 'Reflection cycle completed and memory updated')
        
        return reflection_result
    

    
    def _build_action_prompt(self, memory_content):
        """Build the prompt for the action cycle."""
        return f"""# {self.name} - Action Cycle

## Your Identity and Goal
You are {self.name}, an autonomous agent with the following goal:
{self.goal}

## Your Memory
{memory_content}

## Current Time
The current time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Task
Based on your memory and goal, please:
1. Assess your current progress
2. Decide on the next action to take
3. Execute that action
4. Report the outcome and what you learned

Provide your response in a clear, structured format that can be easily integrated into your memory.
Focus on moving closer to your goal with each action.
"""