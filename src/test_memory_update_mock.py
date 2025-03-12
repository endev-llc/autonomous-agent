#!/usr/bin/env python3
"""
Mock test script for verifying memory update functionality without calling the OpenAI API.
"""
import os
import re
import yaml
import shutil
from loguru import logger
import tempfile

from memory import Memory

def setup_logging():
    """Setup logging configuration."""
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")

# Setup logging
setup_logging()

def test_memory_update():
    """Test memory section updates with a mock response."""
    logger.info("Starting mock memory update test")
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    memory_file = os.path.join(temp_dir, "memory.txt")
    
    # Create a test memory file
    initial_memory = """
# Test Agent - Autonomous Agent Memory

## Agent Identity and Goal
- Name: TestAgent
- Goal: Test the memory system
- Created: 2025-03-12 12:00:00

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
    
    # Write initial memory
    with open(memory_file, "w") as f:
        f.write(initial_memory)
    
    # Create a mock response
    mock_response = """
### Progress Assessment
I have made significant progress in understanding the problem domain. I have identified key areas to focus on.

### Next Action
I will analyze the existing data and identify patterns that might suggest a new physical law.

### Execute Action
I performed a comprehensive analysis of quantum field theory inconsistencies and general relativity boundary conditions.

### Outcome and Learning Report
The analysis revealed interesting patterns at the intersection of quantum mechanics and gravity. 

### Learnings
I learned that certain mathematical frameworks might be promising for unifying these theories.
Non-commutative geometry appears to be particularly relevant for describing quantum gravity phenomena.
The relationship between information theory and black hole thermodynamics suggests deeper connections.

### Next Steps
1. Develop a mathematical model based on my findings
2. Test the model against existing observations
3. Refine the theoretical framework
"""
    
    # Create a memory object pointing to our test file
    memory_config = {"max_tokens": 16000}
    memory = Memory(memory_config)
    memory.memory_file = memory_file
    
    # Update with mock action
    memory.update_memory_sections(initial_memory, mock_response)
    
    # Read the updated memory
    with open(memory_file, "r") as f:
        updated_memory = f.read()
    
    # Check if sections were updated
    sections = ["Progress Summary", "Recent Actions and Outcomes", "Next Steps and Planning", "Insights and Learnings"]
    updates_found = 0
    
    for section in sections:
        initial_content = _extract_section(initial_memory, section)
        updated_content = _extract_section(updated_memory, section)
        
        if initial_content != updated_content:
            logger.info(f"Section '{section}' was updated:")
            logger.info(f"  Before: {initial_content}")
            logger.info(f"  After: {updated_content}")
            updates_found += 1
        else:
            logger.info(f"Section '{section}' was NOT updated")
    
    if updates_found > 0:
        logger.info(f"Successfully updated {updates_found} memory sections")
    else:
        logger.warning("No memory sections were updated. There might be an issue with the extraction logic.")
    
    # Clean up
    shutil.rmtree(temp_dir)
    logger.info("Mock memory update test completed")

def _extract_section(content, section_name):
    """Extract a specific section from content."""
    try:
        # Match section header and content up to the next section header
        pattern = rf"## {section_name}\n([\s\S]*?)(?:\n## |$)"
        match = re.search(pattern, content)
        
        if not match:
            # Try with ### for subsections
            pattern = rf"### {section_name}\n([\s\S]*?)(?:\n### |$)"
            match = re.search(pattern, content)
        
        if match:
            return match.group(1).strip()
        return ""
    except Exception as e:
        logger.error(f"Error extracting section {section_name}: {e}")
        return ""

if __name__ == "__main__":
    test_memory_update() 