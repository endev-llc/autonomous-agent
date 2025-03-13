"""
Agent module that coordinates the agent's operations.
"""
import os
import json
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
            
        # Initialize findings log
        self.findings_log = os.path.join("data", "findings", "findings_log.md")
        if not os.path.exists(self.findings_log):
            self._initialize_findings_log()
            
        # Initialize connections log
        self.connections_log = os.path.join("data", "connections", "connections_log.md")
        if not os.path.exists(self.connections_log):
            self._initialize_connections_log()
            
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

## Web Search Topics
Potential topics to search for on the web:
1. Current theoretical physics inconsistencies
2. Unexplained physical phenomena
3. Recent advances in theoretical physics
4. Patterns in physical constants

## Action Summaries
Recent actions taken by the agent.
"""
        self.memory.write(initial_memory)
        logger.info("Agent memory initialized")
        
    def _initialize_findings_log(self):
        """Initialize the findings log file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.findings_log), exist_ok=True)
            
            # Create the initial findings log
            initial_content = f"""# {self.name} - Physics Findings Log

## Overview
This log contains all notable findings discovered by {self.name} in the pursuit of:

**Goal**: {self.goal}

*Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## Findings
No findings recorded yet.

"""
            # Write to file
            with open(self.findings_log, "w") as f:
                f.write(initial_content)
                
            logger.info("Findings log initialized")
        except Exception as e:
            logger.error(f"Error initializing findings log: {e}")
    
    def _initialize_connections_log(self):
        """Initialize the connections log file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.connections_log), exist_ok=True)
            
            # Create the initial connections log
            initial_content = f"""# {self.name} - Connections Log

## Overview
This log contains connections between concepts, theories, and observations identified by {self.name} in the pursuit of:

**Goal**: {self.goal}

*Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## Connections
No connections recorded yet.

"""
            # Write to file
            with open(self.connections_log, "w") as f:
                f.write(initial_content)
                
            logger.info("Connections log initialized")
        except Exception as e:
            logger.error(f"Error initializing connections log: {e}")
    
    def run_action_cycle(self):
        """Run a single action cycle."""
        logger.info("Running action cycle")
        
        # Read memory
        memory_content = self.memory.read()
        
        # Prepare prompt for the model, using the improved focused prompt
        prompt = self._build_focused_action_prompt(memory_content)
        
        # Log we're about to call the model
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('info', f'Running action cycle and sending prompt to model')
        
        # Get response from the model
        response = self.model.query(prompt)
        
        # Check if there are web search commands in the response
        search_queries = self._extract_search_queries(response)
        if search_queries:
            search_results = self._perform_web_searches(search_queries)
            # Analyze search results and update response
            analysis_result = self._analyze_search_results(search_queries, search_results)
            response += f"\n\n### Web Search Results and Analysis\n{analysis_result}"
        
        # Ensure we capture and log findings - even if not explicitly marked
        explicitly_marked_findings = self._extract_findings(response)
        if not explicitly_marked_findings:
            # If no explicit findings markers, extract implicit findings
            implicit_findings = self._extract_implicit_findings(response)
            if implicit_findings:
                for finding in implicit_findings:
                    self._record_finding(finding['title'], finding['content'])
        else:
            # Process explicitly marked findings
            for finding in explicitly_marked_findings:
                self._record_finding(finding['title'], finding['content'])
        
        # Check if there are connection commands in the response
        connections = self._extract_connections(response)
        if connections:
            for connection in connections:
                self._record_connection(connection['title'], connection['content'])
        
        # If no explicit connections found, try to extract implicit connections
        if not connections:
            implicit_connections = self._extract_implicit_connections(response)
            if implicit_connections:
                for connection in implicit_connections:
                    self._record_connection(connection['title'], connection['content'])
        
        # Check if there's a discovery declaration in the response
        self._check_for_discovery(response)
        
        # Update memory with the response, using a more efficient approach
        self.memory.update_with_action_efficiently(response)
        
        # Log memory update
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('info', f'Updated memory with action result')
        
        # Log action
        logger.info(f"Action completed, memory updated")
        
        # Log to web interface if model has web server
        if hasattr(self.model, 'web_server') and self.model.web_server:
            self.model.web_server.log_interaction('action', 'Action cycle completed and memory updated')
            
        return response
    
    def _extract_search_queries(self, response):
        """Extract web search queries from response."""
        search_pattern = r'### WEB_SEARCH\s*\n(.*?)(?=###|$)'
        matches = re.finditer(search_pattern, response, re.DOTALL)
        
        queries = []
        for match in matches:
            query_text = match.group(1).strip()
            # Split by lines and remove empty lines
            query_lines = [line.strip() for line in query_text.split('\n') if line.strip()]
            queries.extend(query_lines)
            
        return queries
        
    def _perform_web_searches(self, queries):
        """Perform web searches for a list of queries."""
        results = {}
        
        for query in queries:
            logger.info(f"Performing web search: {query}")
            
            # Log to web interface if model has web server
            if hasattr(self.model, 'web_server') and self.model.web_server:
                self.model.web_server.log_interaction('search', f'Searching for: {query}')
                
            # Perform the search
            search_result = self.model.web_search(query)
            
            # Store the result
            results[query] = search_result
            
        return results
    
    def _analyze_search_results(self, queries, results):
        """Analyze the collected search results."""
        analysis_text = ""
        
        for query in queries:
            if query in results:
                logger.info(f"Analyzing search results for: {query}")
                
                # Log to web interface if model has web server
                if hasattr(self.model, 'web_server') and self.model.web_server:
                    self.model.web_server.log_interaction('analyze', f'Analyzing results for: {query}')
                
                # Analyze the results
                analysis = self.model.analyze_search_results(query, results[query])
                
                # Add to the full analysis text
                analysis_text += f"\n\n#### Search Query: {query}\n{analysis}\n"
        
        return analysis_text
    
    def _extract_connections(self, response):
        """Extract connections from response."""
        connection_pattern = r'### CONNECTION\s*\n(.*?)(?=###|$)'
        matches = re.finditer(connection_pattern, response, re.DOTALL)
        
        connections = []
        for match in matches:
            connection_text = match.group(1).strip()
            # Extract title and content
            parts = connection_text.split('\n', 1)
            if len(parts) >= 2:
                title = parts[0].strip()
                content = parts[1].strip()
                connections.append({
                    'title': title,
                    'content': content
                })
            
        return connections
    
    def _record_connection(self, title, content):
        """Record a connection to the connections log."""
        try:
            logger.info(f"Recording connection: {title}")
            
            # Create a file for this connection
            self.model.record_connection(title, content)
            
            # Update the connections log
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_entry = f"\n### {timestamp} - {title}\n{content}\n"
            
            # Read current log
            with open(self.connections_log, "r") as f:
                log_content = f.read()
            
            # Insert new entry before the last line
            if "No connections recorded yet." in log_content:
                # Replace the placeholder
                log_content = log_content.replace("No connections recorded yet.", new_entry.strip())
            else:
                # Append to the list
                log_content = log_content.rstrip() + new_entry
            
            # Write updated log
            with open(self.connections_log, "w") as f:
                f.write(log_content)
                
            # Log to web interface if model has web server
            if hasattr(self.model, 'web_server') and self.model.web_server:
                self.model.web_server.log_interaction('connection', f'Recorded connection: {title}')
                
            return True
        except Exception as e:
            logger.error(f"Error recording connection: {e}")
            return False
    
    def _extract_findings(self, response):
        """Extract findings from response."""
        finding_pattern = r'### FINDING\s*\n(.*?)(?=###|$)'
        matches = re.finditer(finding_pattern, response, re.DOTALL)
        
        findings = []
        for match in matches:
            finding_text = match.group(1).strip()
            # Extract title and content
            parts = finding_text.split('\n', 1)
            if len(parts) >= 2:
                title = parts[0].strip()
                content = parts[1].strip()
                findings.append({
                    'title': title,
                    'content': content
                })
            
        return findings
    
    def _record_finding(self, title, content):
        """Record a finding to the findings log."""
        try:
            logger.info(f"Recording finding: {title}")
            
            # Create the findings directory if it doesn't exist
            findings_dir = os.path.join("data", "findings")
            os.makedirs(findings_dir, exist_ok=True)
            
            # Create a filename based on the title and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            title_slug = title.lower().replace(' ', '_')[:30]  # Create a slug from the title
            filename = f"{timestamp}_{title_slug}.md"
            filepath = os.path.join(findings_dir, filename)
            
            # Format the content
            formatted_content = f"""# Finding: {title}
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

{content}
"""
            
            # Write finding to file
            with open(filepath, 'w') as f:
                f.write(formatted_content)
            
            # Update the findings log
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_entry = f"\n### {timestamp_str} - {title}\n{content}\n"
            
            # Read current log
            with open(self.findings_log, "r") as f:
                log_content = f.read()
            
            # Insert new entry before the last line
            if "No findings recorded yet." in log_content:
                # Replace the placeholder
                log_content = log_content.replace("No findings recorded yet.", new_entry.strip())
            else:
                # Append to the list
                log_content = log_content.rstrip() + new_entry
            
            # Write updated log
            with open(self.findings_log, "w") as f:
                f.write(log_content)
                
            # Log to web interface if model has web server
            if hasattr(self.model, 'web_server') and self.model.web_server:
                self.model.web_server.log_interaction('finding', f'Recorded finding: {title}')
                
            return True
        except Exception as e:
            logger.error(f"Error recording finding: {e}")
            return False
    
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
    
    def _build_focused_action_prompt(self, memory_content):
        """Build an improved, more focused prompt for the action cycle."""
        # Extract essential sections from memory
        identity_section = self._extract_section(memory_content, "Agent Identity and Goal")
        progress_section = self._extract_section(memory_content, "Progress Summary")
        next_steps_section = self._extract_section(memory_content, "Next Steps and Planning")
        recent_actions = self._extract_section(memory_content, "Recent Actions and Outcomes")
        insights_section = self._extract_section(memory_content, "Insights and Learnings")
        action_summaries = self._extract_section(memory_content, "Action Summaries")
        
        # Check if we have any findings or connections
        findings_files = []
        connections_files = []
        
        findings_dir = os.path.join("data", "findings")
        connections_dir = os.path.join("data", "connections")
        
        if os.path.exists(findings_dir):
            findings_files = [f for f in os.listdir(findings_dir) if f.endswith('.md') and not f == "findings_log.md"]
            findings_files.sort(reverse=True)  # Most recent first
        
        if os.path.exists(connections_dir):
            connections_files = [f for f in os.listdir(connections_dir) if f.endswith('.md') and not f == "connections_log.md"]
            connections_files.sort(reverse=True)  # Most recent first
        
        # Get the most recent findings and connections (up to 3 each)
        recent_findings_summary = ""
        if findings_files:
            recent_findings_summary += "## Recent Findings\n"
            for i, filename in enumerate(findings_files[:3]):
                try:
                    with open(os.path.join(findings_dir, filename), 'r') as f:
                        content = f.read()
                        # Extract title and first paragraph
                        title_match = re.search(r'# Finding: (.*?)\n', content)
                        if title_match:
                            title = title_match.group(1)
                            # Extract first paragraph after timestamp line
                            timestamp_line_pos = content.find('*Generated on:')
                            if timestamp_line_pos != -1:
                                content_after_timestamp = content[content.find('\n', timestamp_line_pos) + 1:]
                                first_para = content_after_timestamp.split('\n\n')[0].strip()
                                recent_findings_summary += f"- **{title}**: {first_para}\n\n"
                except Exception as e:
                    logger.error(f"Error reading finding file {filename}: {e}")
        
        recent_connections_summary = ""
        if connections_files:
            recent_connections_summary += "## Recent Connections\n"
            for i, filename in enumerate(connections_files[:3]):
                try:
                    with open(os.path.join(connections_dir, filename), 'r') as f:
                        content = f.read()
                        # Extract title and first paragraph
                        title_match = re.search(r'# Connection: (.*?)\n', content)
                        if title_match:
                            title = title_match.group(1)
                            # Extract first paragraph after timestamp line
                            timestamp_line_pos = content.find('*Generated on:')
                            if timestamp_line_pos != -1:
                                content_after_timestamp = content[content.find('\n', timestamp_line_pos) + 1:]
                                first_para = content_after_timestamp.split('\n\n')[0].strip()
                                recent_connections_summary += f"- **{title}**: {first_para}\n\n"
                except Exception as e:
                    logger.error(f"Error reading connection file {filename}: {e}")
        
        # Create focused prompt with emphasis on making progress toward the goal
        return f"""# {self.name} - Focused Action Cycle

## Your Goal
As {self.name}, your goal is to:
{self.goal}

## Your Current Status

### Identity and Goal
{identity_section}

### Progress Summary
{progress_section}

### Recent Actions
{recent_actions}

## Important Context

### Key Insights Gathered
{insights_section}

### Recent Findings
{recent_findings_summary if recent_findings_summary else "No recent findings documented yet."}

### Recent Connections
{recent_connections_summary if recent_connections_summary else "No recent connections documented yet."}

### Action Summaries
{action_summaries if action_summaries else "No recent action summaries available yet."}

### Next Steps Planned
{next_steps_section}

## Current Time
The current time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Your Task

As a scientific agent working on discovering a new law of physics, your priority should be to:

1. MAKE SUBSTANTIVE PROGRESS toward your goal by applying scientific methodology:
   - Formulate testable hypotheses
   - Seek evidence and theoretical foundations
   - Analyze patterns in existing data
   - Develop mathematical frameworks

2. DOCUMENT YOUR THINKING PROCESS using the sections below, ensuring you capture:
   - Concrete findings that contribute to scientific knowledge
   - Connections between different concepts, theories or observations
   - Critical analyses of existing physical models and their inconsistencies
   - Novel mathematical or theoretical frameworks

3. AVOID REPETITIVE WEB SEARCHES:
   - Don't search for the same information repeatedly
   - Build on previously gathered information
   - Use search strategically to fill knowledge gaps
   - Focus on synthesizing information rather than just collecting it

## Response Format

Structure your response with these exact sections to ensure your progress is properly documented:

### Progress Assessment
Evaluate your current progress toward discovering a new law of physics. Be specific about what you've learned and what remains uncertain.

### Next Action
Describe ONE specific, concrete action you will take next toward your goal. This should be a substantive step, not just "continue researching." What specific hypothesis, pattern, or theory will you investigate now?

### Execute Action
Describe how you executed the action, providing substantive scientific reasoning and analysis.

### FINDING
Record at least one notable scientific finding from this action cycle. Include a clear title and detailed explanation.
Title of your finding
Detailed explanation of the finding, including its scientific significance and how it contributes to your goal of discovering a new law of physics.

### CONNECTION
Record at least one connection between concepts, theories, or observations. Include a clear title and detailed explanation.
Title of the connection
Detailed explanation of how these concepts are connected and why this connection is significant for physics.

### Outcome and Learning Report
Summarize what you learned from this action and how it advances your understanding of physics.

### Learnings
Extract 3-5 key insights from this action cycle that represent your growing understanding.

### Next Steps
Outline 2-3 specific next steps based on what you just learned. These should be concrete actions that build on your findings.

### WEB_SEARCH
If you need new information, include up to 3 specific, targeted search queries on separate lines. Don't repeat previous searches.

## DISCOVERY DECLARATION
Include this ONLY if you have formulated a truly novel, mathematical law or theory of physics that meets all criteria:
1. Has precise mathematical formulation
2. Explains previously unexplained phenomena 
3. Makes testable predictions
4. Shows consistency with established laws where they are valid
5. Identifies where and why existing theories fail
"""
    
    def _extract_section(self, content, section_name):
        """Extract a specific section from content."""
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
        """Extract the most recent custom sections from memory."""
        try:
            # Find all sections that start with a timestamp (likely recent activities)
            pattern = r"## Action Taken at ([0-9\-: ]+)\n([\s\S]*?)(?=\n## Action Taken at|\Z)"
            matches = list(re.finditer(pattern, content))
            
            # Get the most recent ones
            recent_matches = matches[-num_sections:] if matches else []
            
            # Format them
            result = ""
            for match in recent_matches:
                timestamp = match.group(1)
                section_content = match.group(2).strip()
                result += f"## Action Taken at {timestamp}\n{section_content}\n\n"
                
            return result.strip()
        except Exception as e:
            logger.error(f"Error extracting recent sections: {e}")
            return ""
    
    def test_memory_update(self):
        """Test updating memory with a sample action."""
        test_response = """
### Progress Assessment
Making initial progress on the goal.

### Next Action
Research quantum gravity theories.

### Execute Action
Executed research on quantum physics.

### Outcome and Learning Report
Learned about quantum entanglement.

### Learnings
The quantum world is strange but fascinating.

### Next Steps
Explore the implications of quantum entanglement.
"""
        
        # Update memory
        result = self.memory.update_with_action(test_response)
        if result:
            return "Memory updated successfully."
        else:
            return "Failed to update memory."

    def _extract_implicit_findings(self, response):
        """Extract potential findings from response even when not explicitly marked."""
        findings = []
        
        # Look for sections that indicate findings without the specific marker
        # Patterns that might indicate findings
        patterns = [
            r'(?:Observation|Finding|Discovery|Insight):\s*(.*?)(?=$|\n\n)',
            r'I (?:found|discovered|observed|noticed):\s*(.*?)(?=$|\n\n)',
            r'(?:Important|Key|Critical) (?:point|result|information):\s*(.*?)(?=$|\n\n)',
            r'(?:Analysis|Results) show(?:s|ed) that:\s*(.*?)(?=$|\n\n)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, response, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                content_text = match.group(1).strip()
                if len(content_text) > 20:  # Only consider substantial findings
                    # Create a title from the first line or first few words
                    title_text = content_text.split('\n')[0][:50]
                    if len(title_text) < 10:  # Title too short, use first few words
                        title_words = content_text.split()[:6]
                        title_text = ' '.join(title_words)
                    
                    findings.append({
                        'title': title_text,
                        'content': content_text
                    })
        
        return findings

    def _extract_implicit_connections(self, response):
        """Extract potential connections from response even when not explicitly marked."""
        connections = []
        
        # Look for sections that indicate connections without the specific marker
        # Patterns that might indicate connections
        patterns = [
            r'(?:Connection|Relationship|Correlation|Link) (?:between|among):\s*(.*?)(?=$|\n\n)',
            r'(?:Related|Connected|Associated):\s*(.*?)(?=$|\n\n)',
            r'(?:This|The above) (?:relates|connects|links) to:\s*(.*?)(?=$|\n\n)',
            r'I (?:see|found) a (?:connection|relationship|correlation):\s*(.*?)(?=$|\n\n)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, response, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                content_text = match.group(1).strip()
                if len(content_text) > 20:  # Only consider substantial connections
                    # Create a title from the first line or first few words
                    title_text = content_text.split('\n')[0][:50]
                    if len(title_text) < 10:  # Title too short, use first few words
                        title_words = content_text.split()[:6]
                        title_text = ' '.join(title_words)
                    
                    connections.append({
                        'title': title_text,
                        'content': content_text
                    })
        
        return connections

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
            web_search_topics = self._extract_section(memory_content, "Web Search Topics")
            
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

## Web Search Topics
{web_search_topics}

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

## Your Capabilities
You have the ability to:
1. Search the web for information
2. Record findings from your research
3. Make connections between ideas and concepts
4. Declare a discovery when you have sufficient evidence

## Task
Based on your memory and goal, please:
1. Assess your current progress
2. Decide on the next action to take
3. Execute that action (which may include web searches)
4. Report the outcome and what you learned
5. Record any notable findings or connections

## Response Format
Please structure your response with the following sections to help me update my memory effectively:

### Progress Assessment
Provide a concise assessment of your current progress toward your goal. This will update the "Progress Summary" section of your memory.

### Next Action
Detail the specific actions you will take next. This will update the "Next Steps and Planning" section of your memory.

### Execute Action
Describe how you executed the action and what happened.

### WEB_SEARCH
If you need to search the web, list each search query on a new line. For example:
quantum gravity experimental evidence
unexplained phenomena in physics
theoretical inconsistencies in standard model

### Outcome and Learning Report
Summarize the outcomes of your action and what you learned from it. This will update the "Recent Actions and Outcomes" section of your memory.

### Learnings
Explain what insights you gained from this action. This will update the "Insights and Learnings" section.

### Next Steps
Outline your immediate next steps based on what you just learned. This will also contribute to updating the "Next Steps and Planning" section.

### FINDING
To record a notable finding, include its title on the first line followed by the detailed content on subsequent lines. For example:
Potential correlation between dark matter distribution and galactic rotation
I've observed that the distribution of dark matter in galaxy clusters shows a pattern that doesn't align with current models. Specifically...

### CONNECTION
To record a connection between concepts, include its title on the first line followed by the detailed explanation on subsequent lines. For example:
Link between quantum entanglement and spacetime curvature
The mathematical structure of quantum entanglement has interesting parallels with the equations describing spacetime curvature in general relativity...

## IMPORTANT: Declaring a Discovery
If and ONLY if you have DEFINITIVELY discovered a new law of physics that is:
1. Novel (not previously known in the field)
2. Mathematically formulated
3. Explains previously unexplained phenomena
4. Has predictive power for new observations

THEN, and only then, include an additional section:

### DISCOVERY_DECLARATION
[Detailed description of the new law of physics, including:
- Its formal mathematical statement
- The phenomena it explains
- Predictions it makes
- How it relates to existing theories]
"""