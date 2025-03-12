"""
Agent module that coordinates the agent's operations.
"""
import os
from datetime import datetime
import re
from loguru import logger

from model_interface import ModelInterface
from memory import Memory

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
        
        # Log we're about to call the model
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('info', f'Running action cycle and sending prompt to model')
        
        # Get response from the model
        response = self.model.query(prompt)
        
        # Update memory with the response
        self.memory.update_with_action(response)
        
        # Log memory update
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('info', f'Updated memory with action result')
        
        # Log action
        logger.info(f"Action completed, memory updated")
        
        # Log to web interface if model has web server
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('action', 'Action cycle completed and memory updated')
            
        return response
    
    def _build_action_prompt(self, memory_content):
        """Build the prompt for the action cycle."""
        # Check if memory content is too large, if so, summarize it
        memory_size = len(memory_content)
        token_estimate = memory_size / 4  # Rough estimate (4 chars per token average)
        
        # Log memory stats
        logger.debug(f"Memory size: {memory_size} characters, ~{token_estimate:.0f} tokens")
        
        # If memory is getting very large, we need a more efficient approach
        # For now, we'll implement a simple memory trimming strategy
        max_memory_chars = 24000  # About 6000 tokens which is reasonable for modern models
        
        if memory_size > max_memory_chars:
            logger.info(f"Memory exceeding size limit ({memory_size} chars), trimming to ~{max_memory_chars} chars")
            
            # Extract essential sections - always keep these
            identity_section = self._extract_section(memory_content, "Agent Identity and Goal")
            progress_section = self._extract_section(memory_content, "Progress Summary")
            next_steps_section = self._extract_section(memory_content, "Next Steps and Planning")
            
            # Only keep the most recent actions and insights
            recent_actions = self._extract_section(memory_content, "Recent Actions and Outcomes")
            insights_section = self._extract_section(memory_content, "Insights and Learnings")
            
            # Recent reflections and actions
            recent_sections = self._extract_recent_sections(memory_content, 3)
            
            # Construct trimmed memory
            trimmed_memory = f"""
# {self.name} - Autonomous Agent Memory

## Agent Identity and Goal
{identity_section}

## Progress Summary
{progress_section}

## Recent Actions and Outcomes
{recent_actions}

## Next Steps and Planning
{next_steps_section}

## Insights and Learnings
{insights_section}

## Recent Activities
{recent_sections}
"""
            
            # Use trimmed memory instead
            memory_content = trimmed_memory
            logger.debug(f"Trimmed memory to {len(memory_content)} chars")
            
            # Optionally log to web server
            if hasattr(self.model, 'web_server') and self.model.web_server:
                self.model.web_server.log_interaction('info', f"Memory trimmed from {memory_size} to {len(memory_content)} chars")
        
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
    
    def _extract_section(self, content, section_name):
        """Extract a specific section from the memory content."""
        try:
            # Match section header and content up to the next section header
            pattern = rf"## {section_name}\n([\s\S]*?)(?:\n## |$)"
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
            return ""
        except Exception as e:
            logger.error(f"Error extracting section {section_name}: {e}")
            return ""
    
    def _extract_recent_sections(self, content, num_sections=3):
        """Extract the most recent action sections."""
        try:
            # Find all action sections
            pattern = r"##\s+(?:Action)\s+.*?\n([\s\S]*?)(?:\n##|$)"
            matches = re.finditer(pattern, content)
            
            # Get the last n sections
            sections = [match.group(0) for match in matches]
            recent = sections[-num_sections:] if sections else []
            
            return "\n\n".join(recent)
        except Exception as e:
            logger.error(f"Error extracting recent sections: {e}")
            return ""