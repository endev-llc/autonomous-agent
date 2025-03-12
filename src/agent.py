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
        
        # Check if there's a discovery declaration in the response
        self._check_for_discovery(response)
        
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
    
    def _check_for_discovery(self, response):
        """Check if the response contains a declaration of a new physics law discovery."""
        # Look for the DISCOVERY_DECLARATION marker in the response
        if "### DISCOVERY_DECLARATION" in response:
            # Extract the discovery content
            discovery_pattern = r'### DISCOVERY_DECLARATION\s*\n([\s\S]*?)(?=###|$)'
            match = re.search(discovery_pattern, response)
            
            if match:
                discovery_content = match.group(1).strip()
                # Record the discovery
                self.record_discovery(discovery_content)
                logger.info(f"New law of physics discovered and recorded!")
                
                # Log to web interface if model has web server
                if hasattr(self.model, 'web_server') and self.model.web_server:
                    self.model.web_server.log_interaction('discovery', 'New law of physics discovered and recorded in findings.txt!')
    
    def record_discovery(self, discovery_content):
        """Record a confirmed new law of physics discovery to findings.txt."""
        try:
            # Create the findings file
            findings_file = "data/findings.txt"
            
            # Ensure data directory exists
            os.makedirs(os.path.dirname(findings_file), exist_ok=True)
            
            # Create a formatted entry
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            formatted_discovery = f"""
# New Law of Physics Discovered by {self.name}
## Date of Discovery: {timestamp}

{discovery_content}
"""
            
            # Write the discovery
            with open(findings_file, "w") as f:
                f.write(formatted_discovery)
                
            logger.info(f"Discovery recorded to {findings_file}")
            return True
        except Exception as e:
            logger.error(f"Error recording discovery: {e}")
            return False
    
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

## Response Format
Please structure your response with the following sections to help me update my memory effectively:

### Progress Assessment
Provide a concise assessment of your current progress toward your goal. This will update the "Progress Summary" section of your memory.

### Next Action
Detail the specific actions you will take next. This will update the "Next Steps and Planning" section of your memory.

### Execute Action
Describe how you executed the action and what happened.

### Outcome and Learning Report
Summarize the outcomes of your action and what you learned from it. This will update the "Recent Actions and Outcomes" section of your memory.

### Learnings
Explain what insights you gained from this action. This will update the "Insights and Learnings" section.

### Next Steps
Outline your immediate next steps based on what you just learned. This will also contribute to updating the "Next Steps and Planning" section.

## IMPORTANT: Declaring a Discovery
If and ONLY if you have DEFINITIVELY discovered a new law of physics that is:
1. Novel (not previously known in the field)
2. Mathematically formulated
3. Explains previously unexplained phenomena
4. Has predictive power for new observations

THEN, and only then, include an additional section:

### DISCOVERY_DECLARATION
[Detailed description of the new law of physics, including:
- The formal statement of the law
- The mathematical formulation
- The phenomena it explains
- Predictions it makes
- How it was derived]

DO NOT use the DISCOVERY_DECLARATION section for hypotheses, partial ideas, or anything that doesn't meet ALL of the criteria above. This will create a permanent record of your discovery in a dedicated findings.txt file.

Please start each section with "### " followed by the exact section names provided above (e.g., "### Progress Assessment"), as this formatting is required for proper memory updates.

Focus on moving closer to your goal with each action.
"""
    
    def _extract_section(self, content, section_name):
        """Extract a specific section from the memory content."""
        # Reuse memory's extract section method
        return self.memory._extract_section(content, section_name)
    
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
            
    def test_memory_update(self):
        """Run a single action cycle and log memory changes for testing."""
        logger.info("Running memory update test")
        
        # Read initial memory
        initial_memory = self.memory.read()
        
        # Extract initial sections for comparison
        initial_sections = {
            "Progress Summary": self._extract_section(initial_memory, "Progress Summary"),
            "Recent Actions and Outcomes": self._extract_section(initial_memory, "Recent Actions and Outcomes"),
            "Next Steps and Planning": self._extract_section(initial_memory, "Next Steps and Planning"),
            "Insights and Learnings": self._extract_section(initial_memory, "Insights and Learnings")
        }
        
        # Run action cycle
        logger.info("Starting action cycle")
        self.run_action_cycle()
        
        # Read updated memory
        updated_memory = self.memory.read()
        
        # Extract updated sections
        updated_sections = {
            "Progress Summary": self._extract_section(updated_memory, "Progress Summary"),
            "Recent Actions and Outcomes": self._extract_section(updated_memory, "Recent Actions and Outcomes"),
            "Next Steps and Planning": self._extract_section(updated_memory, "Next Steps and Planning"),
            "Insights and Learnings": self._extract_section(updated_memory, "Insights and Learnings")
        }
        
        # Log changes
        for section in initial_sections:
            if initial_sections[section] != updated_sections[section]:
                logger.info(f"Section '{section}' was updated")
                logger.info(f"Before: {initial_sections[section]}")
                logger.info(f"After: {updated_sections[section]}")
            else:
                logger.info(f"Section '{section}' was NOT updated")
        
        return {
            "initial": initial_sections,
            "updated": updated_sections
        }