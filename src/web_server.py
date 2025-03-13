"""
Web server module to expose agent state and provide a dashboard interface.
"""
import os
import json
import threading
import markdown
import glob
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from loguru import logger

class WebServer:
    """Web server for exposing agent state and dashboard."""
    
    def __init__(self, agent, host='0.0.0.0', port=8080):
        """Initialize the web server."""
        self.agent = agent
        self.host = host
        self.port = port
        # Determine the static folder path
        # In Docker, we need to use the absolute path from the app root
        web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')
        if not os.path.exists(web_dir):
            # If not found, try relative to current working directory (Docker case)
            web_dir = os.path.join(os.getcwd(), 'web')
            if not os.path.exists(web_dir):
                # Last resort - hardcode the Docker path
                web_dir = '/app/web'
        
        logger.info(f"Using web directory: {web_dir}")
        self.app = Flask(__name__, 
                          static_folder=web_dir,
                          static_url_path='')
        self.interaction_logs = []
        self.max_logs = 100
        self.latest_prompt = None
        self.latest_response = None
        self.interactions_history = []  # Store complete interaction history
        self.max_interactions = 50      # Maximum number of stored interactions
        self.start_time = datetime.now()  # Record when the server started
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up the API routes."""
        # Dashboard route
        @self.app.route('/')
        def index():
            return send_from_directory(self.app.static_folder, 'index.html')
            
        # Health check HTML page
        @self.app.route('/health')
        def health():
            return send_from_directory(self.app.static_folder, 'health.html')
            
        # Test route for diagnostics
        @self.app.route('/test')
        def test():
            return jsonify({
                'status': 'ok',
                'message': 'Web server is running',
                'static_folder': self.app.static_folder,
                'static_folder_exists': os.path.exists(self.app.static_folder),
                'index_exists': os.path.exists(os.path.join(self.app.static_folder, 'index.html')),
                'files_in_static': os.listdir(self.app.static_folder) if os.path.exists(self.app.static_folder) else []
            })
        
        # API routes
        @self.app.route('/api/agent')
        def agent_info():
            return jsonify({
                'name': self.agent.name,
                'goal': self.agent.goal,
                'model': self.agent.model.model_id,
                'startTime': self.start_time.isoformat(),
                'has_discovery': self.has_discovery(),
                'has_findings': self.has_findings(),
                'has_connections': self.has_connections(),
                'has_search_results': self.has_search_results()
            })
        
        @self.app.route('/api/memory')
        def memory():
            memory_content = self.agent.memory.read()
            return jsonify({
                'content': memory_content
            })
        
        @self.app.route('/api/logs')
        def logs():
            limit = request.args.get('limit', default=100, type=int)
            logs = self.interaction_logs[-limit:] if limit > 0 else self.interaction_logs
            return jsonify(logs)
        
        @self.app.route('/api/logs/since')
        def logs_since():
            timestamp = request.args.get('timestamp', default=None)
            if timestamp:
                try:
                    since = datetime.fromisoformat(timestamp)
                    new_logs = [log for log in self.interaction_logs if datetime.fromisoformat(log['timestamp']) > since]
                    return jsonify(new_logs)
                except ValueError:
                    return jsonify({'error': 'Invalid timestamp format'}), 400
            return jsonify([])
            
        @self.app.route('/api/latest-interaction')
        def latest_interaction():
            result = {
                'prompt': self.latest_prompt,
                'response': self.latest_response
            }
            return jsonify(result)
            
        @self.app.route('/api/interactions')
        def interactions_history():
            limit = request.args.get('limit', default=50, type=int)
            return jsonify(self.interactions_history[-limit:] if limit > 0 else self.interactions_history)
        
        # Findings endpoints
        @self.app.route('/api/findings')
        def get_findings():
            findings = self.get_findings_content()
            if findings:
                return jsonify({
                    'exists': True,
                    'content': findings,
                    'html': markdown.markdown(findings)
                })
            else:
                return jsonify({
                    'exists': False,
                    'content': "",
                    'html': ""
                })
                
        @self.app.route('/api/findings/log')
        def get_findings_log():
            try:
                findings_log = os.path.join("data", "findings", "findings_log.md")
                if os.path.exists(findings_log):
                    with open(findings_log, 'r') as f:
                        content = f.read()
                    return jsonify({
                        'exists': True,
                        'content': content,
                        'html': markdown.markdown(content)
                    })
                return jsonify({
                    'exists': False,
                    'content': "",
                    'html': ""
                })
            except Exception as e:
                logger.error(f"Error reading findings log: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/findings/all')
        def get_all_findings():
            try:
                findings_dir = os.path.join("data", "findings")
                findings_files = glob.glob(os.path.join(findings_dir, "*.md"))
                findings_files = [f for f in findings_files if not f.endswith("findings_log.md")]
                
                findings = []
                for file_path in sorted(findings_files, reverse=True):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    filename = os.path.basename(file_path)
                    # Extract timestamp and title from filename
                    timestamp = filename.split('_')[0]
                    findings.append({
                        'id': filename,
                        'filename': filename,
                        'timestamp': timestamp,
                        'content': content,
                        'html': markdown.markdown(content)
                    })
                return jsonify(findings)
            except Exception as e:
                logger.error(f"Error reading all findings: {e}")
                return jsonify({'error': str(e)}), 500
                
        # Connections endpoints
        @self.app.route('/api/connections/log')
        def get_connections_log():
            try:
                connections_log = os.path.join("data", "connections", "connections_log.md")
                if os.path.exists(connections_log):
                    with open(connections_log, 'r') as f:
                        content = f.read()
                    return jsonify({
                        'exists': True,
                        'content': content,
                        'html': markdown.markdown(content)
                    })
                return jsonify({
                    'exists': False,
                    'content': "",
                    'html': ""
                })
            except Exception as e:
                logger.error(f"Error reading connections log: {e}")
                return jsonify({'error': str(e)}), 500
                
        @self.app.route('/api/connections/all')
        def get_all_connections():
            try:
                connections_dir = os.path.join("data", "connections")
                connections_files = glob.glob(os.path.join(connections_dir, "*.md"))
                connections_files = [f for f in connections_files if not f.endswith("connections_log.md")]
                
                connections = []
                for file_path in sorted(connections_files, reverse=True):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    filename = os.path.basename(file_path)
                    # Extract timestamp and title from filename
                    timestamp = filename.split('_')[0]
                    connections.append({
                        'id': filename,
                        'filename': filename,
                        'timestamp': timestamp,
                        'content': content,
                        'html': markdown.markdown(content)
                    })
                return jsonify(connections)
            except Exception as e:
                logger.error(f"Error reading all connections: {e}")
                return jsonify({'error': str(e)}), 500
                
        # Search results endpoints
        @self.app.route('/api/search_results/all')
        def get_all_search_results():
            try:
                search_dir = os.path.join("data", "search_results")
                search_files = glob.glob(os.path.join(search_dir, "*.json"))
                
                search_results = []
                for file_path in sorted(search_files, reverse=True):
                    with open(file_path, 'r') as f:
                        result = json.load(f)
                    filename = os.path.basename(file_path)
                    search_results.append({
                        'id': filename,
                        'filename': filename,
                        'query': result.get('query', ''),
                        'timestamp': result.get('timestamp', ''),
                        'results': result.get('results', {})
                    })
                return jsonify(search_results)
            except Exception as e:
                logger.error(f"Error reading search results: {e}")
                return jsonify({'error': str(e)}), 500
                
        # Analyses endpoints
        @self.app.route('/api/analyses/all')
        def get_all_analyses():
            try:
                analyses_dir = os.path.join("data", "analyses")
                analyses_files = glob.glob(os.path.join(analyses_dir, "*.md"))
                
                analyses = []
                for file_path in sorted(analyses_files, reverse=True):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    filename = os.path.basename(file_path)
                    # Extract timestamp and query from filename
                    parts = filename.split('_')
                    timestamp = parts[0]
                    query = '_'.join(parts[1:-1]) if len(parts) > 2 else ''
                    analyses.append({
                        'id': filename,
                        'filename': filename,
                        'timestamp': timestamp,
                        'query': query,
                        'content': content,
                        'html': markdown.markdown(content)
                    })
                return jsonify(analyses)
            except Exception as e:
                logger.error(f"Error reading analyses: {e}")
                return jsonify({'error': str(e)}), 500
    
    def log_interaction(self, log_type, message):
        """Log an interaction for the dashboard."""
        log_entry = {
            'type': log_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.interaction_logs.append(log_entry)
        
        # Also log to console for debugging
        logger.debug(f"Logged {log_type}: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        # Keep log size manageable
        if len(self.interaction_logs) > self.max_logs:
            self.interaction_logs = self.interaction_logs[-self.max_logs:]
        
        return log_entry
    
    def log_prompt(self, prompt):
        """Log a prompt sent to the model."""
        # Store a shortened version in the log
        shortened = prompt
        if len(prompt) > 200:
            shortened = prompt[:197] + '...'
        
        # Add the log entry
        log_entry = self.log_interaction('prompt', shortened)
        
        # Store the full prompt for the Latest Interaction panel
        self.latest_prompt = {
            'content': prompt,
            'timestamp': log_entry['timestamp']
        }
        
        # Save for interactions history
        self._current_interaction = {
            'prompt': self.latest_prompt,
            'response': None,
            'timestamp': log_entry['timestamp']
        }
        
        return log_entry
    
    def log_response(self, response):
        """Log a response from the model."""
        # Store a shortened version in the log
        shortened = response
        if len(response) > 200:
            shortened = response[:197] + '...'
        
        # Add the log entry
        log_entry = self.log_interaction('response', shortened)
        
        # Store the full response for the Latest Interaction panel
        self.latest_response = {
            'content': response,
            'timestamp': log_entry['timestamp']
        }
        
        # Complete the current interaction and add to history
        if hasattr(self, '_current_interaction') and self._current_interaction and self._current_interaction['prompt']:
            self._current_interaction['response'] = self.latest_response
            
            # Add to interactions history
            self.interactions_history.append(self._current_interaction)
            
            # Limit the history size
            if len(self.interactions_history) > self.max_interactions:
                self.interactions_history = self.interactions_history[-self.max_interactions:]
                
            # Clear current interaction
            self._current_interaction = None
        
        return log_entry
    
    def start(self):
        """Start the web server in a separate thread."""
        logger.info(f"Starting web server on http://{self.host}:{self.port}")
        threading.Thread(target=self._run_server, daemon=True).start()
    
    def _run_server(self):
        """Run the Flask server."""
        try:
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Error starting web server: {e}")

    def has_discovery(self):
        """Check if a findings.txt file exists."""
        findings_file = os.path.join("data", "findings.txt")
        return os.path.exists(findings_file) and os.path.getsize(findings_file) > 0
    
    def has_findings(self):
        """Check if there are any findings."""
        findings_dir = os.path.join("data", "findings")
        return os.path.exists(findings_dir) and len(glob.glob(os.path.join(findings_dir, "*.md"))) > 0
    
    def has_connections(self):
        """Check if there are any connections."""
        connections_dir = os.path.join("data", "connections")
        return os.path.exists(connections_dir) and len(glob.glob(os.path.join(connections_dir, "*.md"))) > 0
    
    def has_search_results(self):
        """Check if there are any search results."""
        search_dir = os.path.join("data", "search_results")
        return os.path.exists(search_dir) and len(glob.glob(os.path.join(search_dir, "*.json"))) > 0
        
    def get_findings_content(self):
        """Get the content of the findings.txt file if it exists."""
        try:
            findings_file = os.path.join("data", "findings.txt")
            if os.path.exists(findings_file) and os.path.getsize(findings_file) > 0:
                with open(findings_file, 'r') as f:
                    return f.read()
            return ""
        except Exception as e:
            logger.error(f"Error reading findings file: {e}")
            return ""
