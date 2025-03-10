// Configuration
const CONFIG = {
    apiBaseUrl: '/api',  // Base URL for API endpoints
    pollInterval: 5000,  // Poll for updates every 5 seconds
    maxLogEntries: 100,  // Maximum number of log entries to display
};

// State management
const state = {
    memory: null,
    logs: [],
    latestInteraction: null,
    agentInfo: null,
    autoScroll: true,
    lastUpdated: null,
};

// DOM Elements
const elements = {
    agentStatus: document.getElementById('agent-status-indicator'),
    agentName: document.getElementById('agent-name'),
    agentGoal: document.getElementById('agent-goal'),
    agentModel: document.getElementById('agent-model'),
    memoryDisplay: document.getElementById('memory-display'),
    logEntries: document.getElementById('log-entries'),
    latestPrompt: document.getElementById('latest-prompt'),
    latestResponse: document.getElementById('latest-response'),
    interactionTimestamp: document.getElementById('interaction-timestamp'),
    interactionProcessingTime: document.getElementById('interaction-processing-time'),
    lastUpdated: document.getElementById('last-updated'),
    clearLogBtn: document.getElementById('clear-log'),
    autoScrollBtn: document.getElementById('auto-scroll'),
    logContainer: document.getElementById('log-container'),
};

// Initialize the dashboard
function initDashboard() {
    // Set up event listeners
    elements.clearLogBtn.addEventListener('click', clearLog);
    elements.autoScrollBtn.addEventListener('click', toggleAutoScroll);
    
    // Start polling for updates
    fetchInitialData();
    setInterval(pollForUpdates, CONFIG.pollInterval);
    
    // Update time
    updateLastUpdated();
    
    // Add simulated data for demo purposes
    if (window.location.search.includes('demo=true')) {
        loadDemoData();
    }
}

// Fetch initial data from the agent
async function fetchInitialData() {
    try {
        // Fetch agent identity
        const agentInfo = await fetchAgentInfo();
        updateAgentInfo(agentInfo);
        
        // Fetch memory
        const memory = await fetchMemory();
        updateMemory(memory);
        
        // Fetch recent logs
        const logs = await fetchLogs();
        updateLogs(logs);
        
        // Fetch latest interaction
        const latestInteraction = await fetchLatestInteraction();
        if (latestInteraction && (latestInteraction.prompt || latestInteraction.response)) {
            updateLatestInteraction(latestInteraction);
        }
        
        // Set agent status to online
        updateAgentStatus('online');
    } catch (error) {
        console.error('Error fetching initial data:', error);
        updateAgentStatus('offline');
        logErrorToUI('Failed to connect to agent API. Is the agent running?');
    }
}

// Poll for updates
async function pollForUpdates() {
    try {
        // Check for new log entries
        const newLogs = await fetchNewLogs();
        if (newLogs && newLogs.length > 0) {
            appendLogs(newLogs);
        }
        
        // Check for latest interaction
        const latestInteraction = await fetchLatestInteraction();
        if (latestInteraction && (latestInteraction.prompt || latestInteraction.response)) {
            updateLatestInteraction(latestInteraction);
        }
        
        // Check for memory updates
        const memory = await fetchMemory();
        updateMemory(memory);
        
        // Update last updated time
        updateLastUpdated();
        
        // Set agent status to online
        updateAgentStatus('online');
    } catch (error) {
        console.error('Error polling for updates:', error);
        updateAgentStatus('offline');
    }
}

// API Methods
async function fetchAgentInfo() {
    // In a real implementation, this would fetch from the API
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/agent-info`);
        if (!response.ok) {
            throw new Error(`Error fetching agent info: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching agent info:', error);
        // Fallback to simulated data
        return simulateApiCall('agentInfo', {
            name: "AutonomousAgent",
            goal: "Research and develop a comprehensive analysis of current AI safety approaches...",
            model: "gpt-4o-2024-08-06",
            startTime: new Date().toISOString()
        });
    }
}

async function fetchMemory() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/memory`);
        if (!response.ok) {
            throw new Error(`Error fetching memory: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching memory:', error);
        // Fallback to simulated data
        return simulateApiCall('memory', {
            content: "# Agent Memory\nNo memory content available."
        });
    }
}

async function fetchLogs(limit = CONFIG.maxLogEntries) {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/logs?limit=${limit}`);
        if (!response.ok) {
            throw new Error(`Error fetching logs: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching logs:', error);
        return [];
    }
}

async function fetchNewLogs(since = state.lastUpdated) {
    if (!since) return [];
    
    try {
        const timestamp = since.toISOString();
        const response = await fetch(`${CONFIG.apiBaseUrl}/logs/since?timestamp=${encodeURIComponent(timestamp)}`);
        if (!response.ok) {
            throw new Error(`Error fetching new logs: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching new logs:', error);
        return [];
    }
}

async function fetchLatestInteraction() {
    // Fetch the latest interaction from the API
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/latest-interaction`);
        if (!response.ok) {
            throw new Error(`Error fetching latest interaction: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching latest interaction:', error);
        return null;
    }
}

// UI Update Methods
function updateAgentInfo(info) {
    if (!info) return;
    
    state.agentInfo = info;
    elements.agentName.textContent = info.name || 'Unknown';
    elements.agentGoal.textContent = info.goal || 'No goal specified';
    elements.agentModel.textContent = info.model || 'Unknown model';
}

function updateMemory(memory) {
    if (!memory || !memory.content) return;
    
    state.memory = memory;
    
    // Convert markdown to HTML for better formatting
    const htmlContent = marked.parse(memory.content);
    elements.memoryDisplay.innerHTML = htmlContent;
}

function updateLogs(logs) {
    if (!logs || !logs.length) return;
    
    // Replace existing logs
    state.logs = logs;
    renderLogs();
}

function appendLogs(newLogs) {
    if (!newLogs || !newLogs.length) return;
    
    // Add new logs to the state
    state.logs = [...state.logs, ...newLogs].slice(-CONFIG.maxLogEntries);
    
    // Append new logs to the UI
    newLogs.forEach(log => {
        appendLogEntry(log);
    });
    
    // Auto-scroll if enabled
    if (state.autoScroll) {
        scrollLogsToBottom();
    }
}

function renderLogs() {
    // Clear existing logs
    elements.logEntries.innerHTML = '';
    
    // Render all logs
    state.logs.forEach(log => {
        appendLogEntry(log);
    });
    
    // Auto-scroll if enabled
    if (state.autoScroll) {
        scrollLogsToBottom();
    }
}

function appendLogEntry(log) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const timestamp = document.createElement('span');
    timestamp.className = 'timestamp';
    timestamp.textContent = formatTimestamp(log.timestamp);
    
    const logType = document.createElement('span');
    logType.className = `log-type ${log.type}`;
    logType.textContent = log.type.toUpperCase();
    
    const message = document.createElement('span');
    message.className = 'message';
    message.textContent = log.message;
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(logType);
    logEntry.appendChild(document.createTextNode(' '));
    logEntry.appendChild(message);
    
    elements.logEntries.appendChild(logEntry);
}

function updateLatestInteraction(interaction) {
    if (!interaction) return;
    
    // Handle different formats of interaction data
    let prompt = '';
    let response = '';
    let timestamp = '';
    
    if (interaction.prompt && typeof interaction.prompt === 'object') {
        prompt = interaction.prompt.content || '';
        timestamp = interaction.prompt.timestamp || '';
    } else if (typeof interaction.prompt === 'string') {
        prompt = interaction.prompt;
    }
    
    if (interaction.response && typeof interaction.response === 'object') {
        response = interaction.response.content || '';
    } else if (typeof interaction.response === 'string') {
        response = interaction.response;
    }
    
    state.latestInteraction = {
        prompt,
        response,
        timestamp
    };
    
    // Update UI with latest interaction
    elements.latestPrompt.textContent = prompt || 'No prompt available';
    elements.latestResponse.innerHTML = response ? marked.parse(response) : 'No response available';
    elements.interactionTimestamp.textContent = formatTimestamp(timestamp || new Date());
    
    // Syntax highlighting
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

function updateAgentStatus(status) {
    elements.agentStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    elements.agentStatus.className = status;
}

function updateLastUpdated() {
    state.lastUpdated = new Date();
    elements.lastUpdated.textContent = formatTimestamp(state.lastUpdated);
}

// UI Event Handlers
function clearLog() {
    state.logs = [];
    elements.logEntries.innerHTML = '';
}

function toggleAutoScroll() {
    state.autoScroll = !state.autoScroll;
    elements.autoScrollBtn.classList.toggle('active', state.autoScroll);
    
    if (state.autoScroll) {
        scrollLogsToBottom();
    }
}

function scrollLogsToBottom() {
    elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
}

function logErrorToUI(message) {
    const errorLog = {
        type: 'error',
        message: message,
        timestamp: new Date()
    };
    
    state.logs.push(errorLog);
    appendLogEntry(errorLog);
}

// Helper Functions
function formatTimestamp(timestamp) {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Simulate API calls (for development/testing)
function simulateApiCall(endpoint, data) {
    return new Promise((resolve) => {
        setTimeout(() => resolve(data), 300);
    });
}

// Generate sample log entries for demo
function generateSampleLogs(count) {
    const types = ['info', 'action', 'prompt', 'response', 'error'];
    const messages = [
        'Agent initialized successfully',
        'Running action cycle',
        'Sending prompt to model API',
        'Response received from model',
        'Updating memory with action result',
        'Performing reflection',
        'Memory updated with reflection',
        'Error: Unable to connect to API',
        'Goal analysis initiated',
        'Research strategy formulated',
        'Beginning literature review on AI safety approaches',
        'Categorizing safety methodologies',
        'Developing evaluation framework',
        'Analyzing effectiveness of containment strategies',
        'Exploring potential improvements to value alignment techniques'
    ];
    
    const logs = [];
    const now = new Date();
    
    for (let i = 0; i < count; i++) {
        const type = types[Math.floor(Math.random() * types.length)];
        const message = messages[Math.floor(Math.random() * messages.length)];
        const timestamp = new Date(now - (count - i) * 60000);
        
        logs.push({
            type,
            message,
            timestamp
        });
    }
    
    return logs;
}

// Demo data for testing
function loadDemoData() {
    // Add example prompt and response
    const examplePrompt = `# AutonomousAgent - Action Cycle

## Your Identity and Goal
You are AutonomousAgent, an autonomous agent with the following goal:
Research and develop a comprehensive analysis of current AI safety approaches, categorize them by methodology, evaluate their effectiveness, and propose potential improvements or novel approaches. Document findings in a structured format that could serve as a reference guide.

## Your Memory
[Memory content displayed above]

## Current Time
The current time is 2025-03-10 08:35:24

## Task
Based on your memory and goal, please:
1. Assess your current progress
2. Decide on the next action to take
3. Execute that action
4. Report the outcome and what you learned

Provide your response in a clear, structured format that can be easily integrated into your memory.
Focus on moving closer to your goal with each action.`;

    const exampleResponse = `# Initial Action: Establishing Research Framework

## Progress Assessment
I am at the beginning of my research journey. I haven't taken any actions yet toward my goal of analyzing AI safety approaches.

## Next Action: Create Research Framework
I will establish a systematic framework for categorizing and evaluating AI safety approaches. This will serve as the foundation for all subsequent research.

## Execution
I've developed the following research framework:

### 1. Primary Categories of AI Safety Approaches
- Containment strategies
- Value alignment techniques
- Technical safety measures
- Governance and policy frameworks
- Monitoring and oversight mechanisms

### 2. Evaluation Criteria
- Theoretical soundness
- Empirical validation
- Scalability to advanced systems
- Implementation feasibility
- Robustness against adversarial scenarios
- Adaptability to novel challenges

### 3. Research Methodology
- Literature review of academic papers
- Analysis of industry best practices
- Examination of existing frameworks
- Identification of gaps and limitations
- Development of novel approaches

## Outcome and Learning
I've established a structured framework that will guide my research. This framework provides:
1. Clear categories for organizing different AI safety approaches
2. Specific criteria for evaluating effectiveness
3. A methodical approach to conducting comprehensive research

I've learned that creating this initial structure is crucial for ensuring systematic and thorough analysis. This framework will help ensure no major approaches or evaluation criteria are overlooked.

## Next Steps
1. Begin literature review focusing on the first category: containment strategies
2. Collect and analyze key papers and approaches in this area
3. Apply evaluation criteria to assess effectiveness
4. Document findings in a structured format`;

    // Update latest interaction
    updateLatestInteraction({
        prompt: examplePrompt,
        response: exampleResponse,
        timestamp: new Date()
    });
    
    // Generate more diverse log entries
    const demoLogs = [
        { type: 'info', message: 'Agent initialized with goal: Research and develop a comprehensive analysis of AI safety approaches...', timestamp: new Date(Date.now() - 600000) },
        { type: 'action', message: 'Running initial action cycle', timestamp: new Date(Date.now() - 540000) },
        { type: 'prompt', message: 'Sending initial prompt to evaluate capabilities and plan approach', timestamp: new Date(Date.now() - 535000) },
        { type: 'response', message: 'Received response with initial research framework', timestamp: new Date(Date.now() - 530000) },
        { type: 'info', message: 'Updating memory with research framework', timestamp: new Date(Date.now() - 525000) },
        { type: 'action', message: 'Beginning literature review on containment strategies', timestamp: new Date(Date.now() - 480000) },
        { type: 'info', message: 'Identified 12 key papers on containment strategies', timestamp: new Date(Date.now() - 420000) },
        { type: 'error', message: 'API rate limit reached - pausing operations for 60 seconds', timestamp: new Date(Date.now() - 390000) },
        { type: 'info', message: 'Operations resumed after rate limit wait', timestamp: new Date(Date.now() - 330000) },
        { type: 'action', message: 'Categorizing containment approaches into formal methods vs. empirical testing', timestamp: new Date(Date.now() - 300000) },
        { type: 'reflection', message: 'Performing scheduled reflection on progress', timestamp: new Date(Date.now() - 240000) },
        { type: 'prompt', message: 'Sending prompt for next action cycle', timestamp: new Date(Date.now() - 180000) },
        { type: 'response', message: 'Received response with analysis of containment strategies', timestamp: new Date(Date.now() - 175000) },
        { type: 'info', message: 'Updating memory with containment strategies analysis', timestamp: new Date(Date.now() - 170000) },
        { type: 'action', message: 'Moving to second category: value alignment techniques', timestamp: new Date(Date.now() - 120000) },
        { type: 'prompt', message: examplePrompt.substring(0, 80) + '...', timestamp: new Date(Date.now() - 60000) },
        { type: 'response', message: exampleResponse.substring(0, 80) + '...', timestamp: new Date(Date.now() - 55000) }
    ];
    
    updateLogs(demoLogs);
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
