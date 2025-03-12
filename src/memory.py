"""
Memory module for managing the agent's memory.
"""
import os
import re
from datetime import datetime
from loguru import logger

class Memory:
    """
    Manages the agent's external memory storage.
    """
    def __init__(self, config):
        """Initialize memory with configuration."""
        self.config = config
        self.memory_file = "data/memory.txt"
        self.max_tokens = config.get("max_tokens", 16000)
        self.structure = config.get("structure", [])
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
    
    def exists(self):
        """Check if the memory file exists."""
        return os.path.exists(self.memory_file) and os.path.getsize(self.memory_file) > 0
    
    def read(self):
        """Read the memory file."""
        try:
            if not self.exists():
                return ""
            
            with open(self.memory_file, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            return ""
    
    def write(self, content):
        """Write content to the memory file."""
        try:
            with open(self.memory_file, "w") as f:
                f.write(content)
            logger.debug("Memory updated")
            return True
        except Exception as e:
            logger.error(f"Error writing memory: {e}")
            return False
    
    def update_with_action(self, action_result):
        """Update memory with the result of an action.
        
        This function overwrites any existing 'Action Taken' entry with the new action.
        """
        try:
            memory_content = self.read()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_action_entry = f"## Action Taken at {timestamp}\n{action_result}\n"
            
            # If any Action Taken entries exist, remove them.
            if "## Action Taken at" in memory_content:
                memory_content = memory_content.split("## Action Taken at")[0].rstrip()
            
            # Parse action result to update core memory sections
            self.update_memory_sections(memory_content, action_result)
            
            # Read the updated memory content
            memory_content = self.read()
            
            # Append the new action
            updated_content = memory_content + "\n\n" + new_action_entry
            
            # Simple token management (approximation)
            if len(updated_content) > self.max_tokens * 4:  # Rough approximation
                half_keep = self.max_tokens * 2
                updated_content = (
                    updated_content[:half_keep] +
                    "\n\n[...Memory truncated...]\n\n" +
                    updated_content[-half_keep:]
                )
            
            return self.write(updated_content)
        except Exception as e:
            logger.error(f"Error updating memory with action: {e}")
            return False
    
    def update_memory_sections(self, memory_content, action_result):
        """Update core memory sections based on the action result."""
        try:
            # Define sections to update and their corresponding patterns in the action result
            sections_to_update = {
                "Progress Summary": ["Progress Assessment", "Current Status", "Observations"],
                "Recent Actions and Outcomes": ["Outcome", "Outcome and Learning Report"],
                "Next Steps and Planning": ["Next Steps", "Next Action"],
                "Insights and Learnings": ["Learnings", "Learning", "Outcome and Learning"]
            }
            
            # Extract current memory sections
            current_sections = {}
            for section_name in sections_to_update.keys():
                current_sections[section_name] = self._extract_section(memory_content, section_name)
            
            # Split action result into sections
            action_sections = self._split_into_sections(action_result)
            
            # Find updates in the action result
            updates = {}
            for memory_section, action_patterns in sections_to_update.items():
                for pattern in action_patterns:
                    if pattern in action_sections:
                        updates[memory_section] = action_sections[pattern]
                        break
            
            # Update the memory file with new section content
            if updates:
                for section_name, content in updates.items():
                    # Only update if there's actual new content
                    if content.strip():
                        memory_content = self._replace_section(memory_content, section_name, content)
                
                # Write updated memory
                self.write(memory_content)
                logger.info(f"Updated core memory sections: {', '.join(updates.keys())}")
        
        except Exception as e:
            logger.error(f"Error updating memory sections: {e}")
    
    def _split_into_sections(self, content):
        """Split content into sections based on ### headers."""
        result = {}
        
        # First, split the content into sections based on ### headers
        section_pattern = r'###\s+([^#\n]+)(?:\n|\r\n?)([\s\S]*?)(?=###\s+[^#\n]+|\Z)'
        matches = re.finditer(section_pattern, content)
        
        for match in matches:
            section_name = match.group(1).strip()
            section_content = match.group(2).strip()
            result[section_name] = section_content
            
        return result
    
    def _extract_section(self, content, section_name):
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
    
    def _replace_section(self, content, section_name, new_content):
        """Replace a specific section in content."""
        try:
            # Format the new section
            formatted_new_content = f"## {section_name}\n{new_content.strip()}"
            
            # Check if section exists
            pattern = rf"## {section_name}\n[\s\S]*?(?=\n## |$)"
            if re.search(pattern, content):
                # Replace existing section
                updated_content = re.sub(
                    pattern,
                    formatted_new_content,
                    content
                )
            else:
                # Section doesn't exist, append it
                updated_content = f"{content.strip()}\n\n{formatted_new_content}"
            
            return updated_content
        except Exception as e:
            logger.error(f"Error replacing section {section_name}: {e}")
            return content
    
    def _clean_section_content(self, content):
        """Clean up section content by removing subsection headers and following content."""
        # Remove subsection headers (### style)
        cleaned_content = re.sub(r'### .*?\n', '', content)
        
        # Remove empty lines that might result from the above
        cleaned_content = re.sub(r'\n\s*\n+', '\n\n', cleaned_content)
        
        return cleaned_content.strip()