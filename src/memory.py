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
    
    def update_with_action_efficiently(self, action_result):
        """Update memory with the result of an action using an improved strategy to manage memory size.
        
        This approach:
        1. Prioritizes recent and important information
        2. Maintains a curated summary of past actions
        3. Prevents memory from growing infinitely
        4. Preserves key insights and learnings
        """
        try:
            memory_content = self.read()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Parse action result to update core memory sections (same as before)
            self.update_memory_sections(memory_content, action_result)
            
            # Read the updated memory content
            memory_content = self.read()
            
            # Split action result into sections for targeted processing
            action_sections = self._split_into_sections(action_result)
            
            # Extract critical information from the action result
            key_insights = self._extract_key_insights(action_result)
            web_search_info = self._extract_web_search_info(action_result)
            
            # Memory optimization: Rather than appending the entire action, 
            # we'll create a summarized version focusing on important elements
            action_summary = self._create_action_summary(action_result, timestamp)
            
            # Get the existing action summaries section or create it
            action_summaries_section = self._extract_section(memory_content, "Action Summaries")
            if not action_summaries_section:
                action_summaries_section = "Recent actions taken by the agent:"
            
            # Add the new summary to the top (most recent first)
            updated_summaries = f"{action_summary}\n\n{action_summaries_section}"
            
            # Limit the number of action summaries to keep
            max_summaries = 5
            summaries_list = updated_summaries.split("\n\n")
            if len(summaries_list) > max_summaries + 1:  # +1 for the header line
                # Keep only the header and the most recent summaries
                updated_summaries = "\n\n".join(summaries_list[:max_summaries + 1])
            
            # Update the memory content with the updated summaries section
            memory_content = self._replace_section(memory_content, "Action Summaries", updated_summaries)
            
            # Update the web search topics if there was a search
            if web_search_info:
                web_topics_section = self._extract_section(memory_content, "Web Search Topics")
                # Ensure we don't duplicate existing topics
                new_topics = []
                for topic in web_search_info:
                    if topic not in web_topics_section:
                        new_topics.append(topic)
                
                if new_topics:
                    updated_web_topics = web_topics_section + "\n" + "\n".join(new_topics)
                    memory_content = self._replace_section(memory_content, "Web Search Topics", updated_web_topics)
            
            # Ensure the memory doesn't exceed the token limit
            if len(memory_content) > self.max_tokens * 4:  # Rough approximation
                memory_content = self._optimize_memory_size(memory_content)
            
            return self.write(memory_content)
        except Exception as e:
            logger.error(f"Error updating memory efficiently: {e}")
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

    def _extract_key_insights(self, action_result):
        """Extract key insights from the action result."""
        insights = []
        
        # Look for explicit insights/learnings section
        learnings_section = None
        
        # Check for ### Learnings section
        learnings_match = re.search(r'### Learnings\s*\n([\s\S]*?)(?=###|$)', action_result)
        if learnings_match:
            learnings_section = learnings_match.group(1).strip()
        
        # If no explicit Learnings section, check for similar sections
        if not learnings_section:
            alternative_patterns = [
                r'### (?:Insights|Learning|Outcome and Learning)\s*\n([\s\S]*?)(?=###|$)',
                r'## (?:Insights|Learnings|Key Takeaways)\s*\n([\s\S]*?)(?=##|$)'
            ]
            
            for pattern in alternative_patterns:
                match = re.search(pattern, action_result)
                if match:
                    learnings_section = match.group(1).strip()
                    break
        
        # If we found a learnings section, process it
        if learnings_section:
            # Split by bullet points or numbered items
            lines = learnings_section.split('\n')
            current_insight = ""
            
            for line in lines:
                line = line.strip()
                # Check if this is a new bullet point/numbered item
                if line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.', line):
                    # Save the previous insight if it exists
                    if current_insight:
                        insights.append(current_insight.strip())
                        current_insight = ""
                    # Start a new insight
                    current_insight = line
                elif line and current_insight:  # Continuation of current insight
                    current_insight += " " + line
            
            # Add the last insight if it exists
            if current_insight:
                insights.append(current_insight.strip())
        
        return insights

    def _extract_web_search_info(self, action_result):
        """Extract web search queries and key points from the action result."""
        search_info = []
        
        # Extract any explicitly marked web search queries
        search_pattern = r'### WEB_SEARCH\s*\n([\s\S]*?)(?=###|$)'
        search_match = re.search(search_pattern, action_result)
        
        if search_match:
            search_text = search_match.group(1).strip()
            # Split by lines and add each non-empty line as a search topic
            for line in search_text.split('\n'):
                if line.strip():
                    search_info.append(f"- {line.strip()}")
        
        return search_info

    def _create_action_summary(self, action_result, timestamp):
        """Create a concise summary of the action for memory storage."""
        # Extract key sections for the summary
        progress = ""
        next_steps = ""
        outcome = ""
        
        # Look for Progress Assessment section
        progress_match = re.search(r'### Progress Assessment\s*\n([\s\S]*?)(?=###|$)', action_result)
        if progress_match:
            progress = progress_match.group(1).strip()
        
        # Look for Outcome section
        outcome_match = re.search(r'### (?:Outcome|Outcome and Learning Report)\s*\n([\s\S]*?)(?=###|$)', action_result)
        if outcome_match:
            outcome = outcome_match.group(1).strip()
        
        # Look for Next Steps section
        next_steps_match = re.search(r'### Next Steps\s*\n([\s\S]*?)(?=###|$)', action_result)
        if next_steps_match:
            next_steps = next_steps_match.group(1).strip()
        
        # Create a summary combining these elements, limited to a reasonable length
        summary = f"**[{timestamp}]** "
        
        if progress:
            # Take only the first sentence or first 100 characters of progress
            first_sentence = re.match(r'([^.!?]+[.!?])', progress)
            if first_sentence:
                summary += f"Progress: {first_sentence.group(1)} "
            else:
                summary += f"Progress: {progress[:100]}... "
        
        if outcome:
            # Take only the first sentence or first 100 characters of outcome
            first_sentence = re.match(r'([^.!?]+[.!?])', outcome)
            if first_sentence:
                summary += f"Outcome: {first_sentence.group(1)} "
            else:
                summary += f"Outcome: {outcome[:100]}... "
        
        if next_steps:
            # For next steps, just indicate how many steps were planned
            steps = [s for s in next_steps.split('\n') if s.strip()]
            summary += f"Planned {len(steps)} next steps."
        
        return summary

    def _optimize_memory_size(self, memory_content):
        """Optimize memory to fit within token limits while preserving important information."""
        # First, extract all important sections
        important_sections = {}
        
        # Always keep these sections in full
        critical_sections = [
            "Agent Identity and Goal",
            "Progress Summary",
            "Next Steps and Planning"
        ]
        
        for section in critical_sections:
            important_sections[section] = self._extract_section(memory_content, section)
        
        # Extract other sections that we'll potentially trim
        trimmable_sections = [
            "Recent Actions and Outcomes",
            "Insights and Learnings",
            "Web Search Topics",
            "Action Summaries"
        ]
        
        for section in trimmable_sections:
            important_sections[section] = self._extract_section(memory_content, section)
        
        # Reconstruct memory, trimming where necessary
        new_memory = f"# Autonomous Agent Memory\n\n"
        
        # Add critical sections unchanged
        for section in critical_sections:
            if important_sections[section]:
                new_memory += f"## {section}\n{important_sections[section]}\n\n"
        
        # Process trimmable sections
        
        # For Recent Actions, keep only the most recent ones
        actions_section = important_sections.get("Recent Actions and Outcomes", "")
        if actions_section:
            # Split into paragraphs and keep only the most recent 3
            paragraphs = actions_section.split('\n\n')
            if len(paragraphs) > 3:
                actions_section = '\n\n'.join(paragraphs[:3])
            new_memory += f"## Recent Actions and Outcomes\n{actions_section}\n\n"
        
        # For Insights, keep all as they're valuable
        insights_section = important_sections.get("Insights and Learnings", "")
        if insights_section:
            new_memory += f"## Insights and Learnings\n{insights_section}\n\n"
        
        # For Web Search Topics, keep recent ones
        web_topics = important_sections.get("Web Search Topics", "")
        if web_topics:
            # Split into lines and keep only the most recent 10 topics
            topics = web_topics.split('\n')
            if len(topics) > 10:
                web_topics = '\n'.join(topics[:10])
            new_memory += f"## Web Search Topics\n{web_topics}\n\n"
        
        # For Action Summaries, keep as is (already limited in update_with_action_efficiently)
        summaries = important_sections.get("Action Summaries", "")
        if summaries:
            new_memory += f"## Action Summaries\n{summaries}\n\n"
        
        return new_memory