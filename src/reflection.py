"""
Reflection module for the agent to assess its progress and update strategy.
"""
from loguru import logger
from datetime import datetime

class Reflection:
    """
    Handles the agent's self-reflection capability.
    """
    def __init__(self, agent):
        """Initialize the reflection module."""
        self.agent = agent
    
    def perform_reflection(self):
        """Perform a reflection to assess progress and update strategy."""
        try:
            # Get current memory
            memory_content = self.agent.memory.read()
            
            # Build reflection prompt
            prompt = self._build_reflection_prompt(memory_content)
            
            # Query the model for reflection
            reflection_result = self.agent.model.query(prompt)
            
            # Update memory with reflection
            self.agent.memory.update_with_reflection(reflection_result)
            
            logger.info("Reflection completed and memory updated")
            return reflection_result
        except Exception as e:
            logger.error(f"Error performing reflection: {e}")
            return None
    
    def _build_reflection_prompt(self, memory_content):
        """Build the prompt for reflection."""
        return f"""# {self.agent.name} - Reflection Session

## Your Identity and Goal
You are {self.agent.name}, an autonomous agent with the following goal:
{self.agent.goal}

## Your Current Memory
{memory_content}

## Reflection Task
Please perform a thorough reflection on your progress toward your goal.
This is a higher-level, more strategic assessment than your regular action cycles.

Please include:

1. **Progress Assessment**: Honestly evaluate your progress toward your goal. What have you accomplished? Where are you falling short?

2. **Strategy Evaluation**: Is your current approach working? What adjustments to your strategy might help you be more effective?

3. **Insights and Patterns**: What patterns or insights have emerged that weren't obvious before? What have you learned that changes how you view your goal or approach?

4. **Obstacles and Solutions**: What obstacles are you facing? What solutions might overcome them?

5. **Next Steps**: Based on this reflection, what should your focus be for the next phase of work?

Provide your reflection in a clear, structured format. Be honest, critical, and constructive.
This reflection will guide your future actions, so make it as useful as possible.
"""