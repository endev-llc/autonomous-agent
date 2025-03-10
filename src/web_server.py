"""
Web server module to expose agent state and provide a dashboard interface.
"""
import os
import json
import threading
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
        @self.app.route('/api/agent-info')
        def agent_info():
            return jsonify({
                'name': self.agent.name,
                'goal': self.agent.goal,
                'model': self.agent.model.model_id,
                'startTime': datetime.now().isoformat()
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
