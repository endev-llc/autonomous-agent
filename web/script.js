// Configuration
const CONFIG = {
    apiBaseUrl: '/api',
    pollInterval: 5000,  // Poll for updates every 5 seconds
    maxInteractions: 20  // Maximum number of interactions to show
};

// Application State
const state = {
    agentInfo: null,
    memory: null,
    logs: [],
    interactions: [],
    lastUpdated: null,
    currentActivity: "Initializing..."
};

// DOM Elements
const elements = {
    // Agent Info
    agentStatus: document.getElementById('agent-status'),
    agentName: document.getElementById('agent-name'),
    agentGoal: document.getElementById('agent-goal'),
    agentModel: document.getElementById('agent-model'),
    agentUptime: document.getElementById('agent-uptime'),
    
    // Current Status
    currentActivity: document.getElementById('current-activity'),
    
    // Memory Tab
    memoryContent: document.getElementById('memory-content'),
    refreshMemory: document.getElementById('refresh-memory'),
    
    // Logs Tab
    logsContainer: document.getElementById('logs-container'),
    refreshLogs: document.getElementById('refresh-logs'),
    
    // Interactions Tab
    interactionsContainer: document.getElementById('interactions-container'),
    refreshInteractions: document.getElementById('refresh-interactions'),
    
    // Modal
    interactionModal: new bootstrap.Modal(document.getElementById('interaction-modal')),
    modalPrompt: document.getElementById('modal-prompt'),
    modalResponse: document.getElementById('modal-response'),
    modalInteractionTime: document.getElementById('modal-interaction-time'),
    
    // Footer
    lastUpdated: document.getElementById('last-updated')
};

// Initialize the dashboard
function init() {
    // Set up event listeners
    setupEventListeners();
    
    // Fetch initial data
    fetchInitialData();
    
    // Start polling for updates
    setInterval(pollForUpdates, CONFIG.pollInterval);
}

// Set up event listeners
function setupEventListeners() {
    // Refresh buttons
    elements.refreshMemory.addEventListener('click', fetchMemory);
    elements.refreshLogs.addEventListener('click', fetchLogs);
    elements.refreshInteractions.addEventListener('click', fetchInteractions);
}

// Fetch initial data
async function fetchInitialData() {
    try {
        // Fetch agent info
        await fetchAgentInfo();
        
        // Fetch memory
        await fetchMemory();
        
        // Fetch logs
        await fetchLogs();
        
        // Fetch interactions
        await fetchInteractions();
        
        // Update agent status
        updateAgentStatus('online');
        
        // Update last updated time
        updateLastUpdated();
    } catch (error) {
        console.error('Error fetching initial data:', error);
        updateAgentStatus('offline');
        showError('Failed to connect to agent API. Is the agent running?');
    }
}

// Poll for updates
async function pollForUpdates() {
    try {
        // Check for new logs
        await fetchLogs();
        
        // Check for new interactions
        await fetchInteractions();
        
        // Update agent status
        updateAgentStatus('online');
        
        // Update last updated time
        updateLastUpdated();
    } catch (error) {
        console.error('Error polling for updates:', error);
        updateAgentStatus('offline');
    }
}

// Fetch agent information
async function fetchAgentInfo() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/agent-info`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        const data = await response.json();
        state.agentInfo = data;
        updateAgentInfo();
        return data;
    } catch (error) {
        console.error('Error fetching agent info:', error);
        throw error;
    }
}

// Fetch memory
async function fetchMemory() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/memory`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        const data = await response.json();
        state.memory = data.content;
        updateMemoryDisplay();
        return data;
    } catch (error) {
        console.error('Error fetching memory:', error);
        throw error;
    }
}

// Fetch logs
async function fetchLogs() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/logs`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        const data = await response.json();
        state.logs = data;
        updateLogsDisplay();
        updateCurrentActivity();
        return data;
    } catch (error) {
        console.error('Error fetching logs:', error);
        throw error;
    }
}

// Fetch all interactions history
async function fetchInteractions() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/interactions?limit=${CONFIG.maxInteractions}`);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        const data = await response.json();
        
        // Check if interactions data has changed before updating display
        if (hasInteractionsChanged(data)) {
            state.interactions = data;
            updateInteractionsDisplay();
        }
        return data;
    } catch (error) {
        console.error('Error fetching interactions:', error);
        throw error;
    }
}

// Check if interactions data has changed
function hasInteractionsChanged(newInteractions) {
    if (state.interactions.length !== newInteractions.length) {
        return true;
    }
    
    // Check if the latest interaction has changed
    if (newInteractions.length > 0 && state.interactions.length > 0) {
        const latest = newInteractions[newInteractions.length - 1];
        const current = state.interactions[state.interactions.length - 1];
        
        if (!latest.prompt || !current.prompt) return true;
        
        // Compare timestamps
        return latest.timestamp !== current.timestamp;
    }
    
    return false;
}

// Update agent info display
function updateAgentInfo() {
    if (state.agentInfo) {
        elements.agentName.textContent = state.agentInfo.name || 'Unknown';
        elements.agentGoal.textContent = state.agentInfo.goal || 'No goal specified';
        elements.agentModel.textContent = state.agentInfo.model || 'Unknown';
        
        // Update uptime if start time is available
        if (state.agentInfo.startTime) {
            updateUptime(state.agentInfo.startTime);
        }
    }
}

// Update memory display
function updateMemoryDisplay() {
    if (state.memory) {
        elements.memoryContent.textContent = state.memory;
    } else {
        elements.memoryContent.textContent = 'No memory data available';
    }
}

// Update logs display
function updateLogsDisplay() {
    if (!state.logs || state.logs.length === 0) {
        elements.logsContainer.innerHTML = '<tr><td colspan="3" class="text-center">No logs available</td></tr>';
        return;
    }
    
    // Clear current logs
    elements.logsContainer.innerHTML = '';
    
    // Add logs (most recent first)
    const recentLogs = state.logs.slice(-50).reverse();
    recentLogs.forEach(log => {
        const row = document.createElement('tr');
        
        // Time cell
        const timeCell = document.createElement('td');
        timeCell.textContent = formatTime(log.timestamp);
        row.appendChild(timeCell);
        
        // Type cell
        const typeCell = document.createElement('td');
        const typeSpan = document.createElement('span');
        typeSpan.className = `log-type ${log.type}`;
        typeSpan.textContent = log.type.charAt(0).toUpperCase() + log.type.slice(1);
        typeCell.appendChild(typeSpan);
        row.appendChild(typeCell);
        
        // Message cell
        const messageCell = document.createElement('td');
        messageCell.textContent = log.message;
        row.appendChild(messageCell);
        
        elements.logsContainer.appendChild(row);
    });
}

// Update interactions display
function updateInteractionsDisplay() {
    if (!state.interactions || state.interactions.length === 0) {
        elements.interactionsContainer.innerHTML = '<div class="text-center py-3">No interactions available</div>';
        return;
    }
    
    // Clear current interactions
    elements.interactionsContainer.innerHTML = '';
    
    // Add interactions (most recent first)
    const sortedInteractions = [...state.interactions].reverse();
    sortedInteractions.forEach((interaction, index) => {
        const interactionElem = createInteractionElement(interaction, index);
        elements.interactionsContainer.appendChild(interactionElem);
    });
}

// Create an interaction element
function createInteractionElement(interaction, index) {
    const container = document.createElement('div');
    container.className = 'interaction-container';
    container.dataset.index = index;
    
    // Interaction header
    const header = document.createElement('div');
    header.className = 'interaction-header';
    
    const interactionNumber = document.createElement('div');
    interactionNumber.textContent = `Interaction #${state.interactions.length - index}`;
    
    const interactionTime = document.createElement('div');
    interactionTime.className = 'interaction-time';
    interactionTime.textContent = formatDateTime(interaction.timestamp || interaction.prompt?.timestamp || '');
    
    header.appendChild(interactionNumber);
    header.appendChild(interactionTime);
    
    // Interaction body
    const body = document.createElement('div');
    body.className = 'interaction-body';
    
    // Prompt section
    const promptSection = document.createElement('div');
    promptSection.className = 'interaction-prompt';
    
    const promptLabel = document.createElement('div');
    promptLabel.className = 'interaction-label';
    promptLabel.innerHTML = '<i class="fas fa-paper-plane"></i> Prompt';
    
    const promptContent = document.createElement('div');
    promptContent.className = 'interaction-content';
    promptContent.textContent = interaction.prompt?.content || 'No prompt available';
    
    promptSection.appendChild(promptLabel);
    promptSection.appendChild(promptContent);
    
    // Response section
    const responseSection = document.createElement('div');
    responseSection.className = 'interaction-response';
    
    const responseLabel = document.createElement('div');
    responseLabel.className = 'interaction-label';
    responseLabel.innerHTML = '<i class="fas fa-reply"></i> Response';
    
    const responseContent = document.createElement('div');
    responseContent.className = 'interaction-content';
    responseContent.textContent = extractTextContent(interaction.response?.content || 'No response available');
    
    responseSection.appendChild(responseLabel);
    responseSection.appendChild(responseContent);
    
    // Add sections to body
    body.appendChild(promptSection);
    body.appendChild(responseSection);
    
    // Add header and body to container
    container.appendChild(header);
    container.appendChild(body);
    
    // Add click event to show full interaction
    container.addEventListener('click', () => showInteractionModal(interaction));
    
    return container;
}

// Show interaction modal with full content
function showInteractionModal(interaction) {
    // Set prompt content
    elements.modalPrompt.textContent = interaction.prompt?.content || 'No prompt available';
    
    // Set response content
    if (interaction.response?.content) {
        try {
            elements.modalResponse.innerHTML = marked.parse(interaction.response.content);
        } catch (e) {
            elements.modalResponse.textContent = interaction.response.content;
        }
    } else {
        elements.modalResponse.textContent = 'No response available';
    }
    
    // Set timestamp
    elements.modalInteractionTime.textContent = formatDateTime(interaction.timestamp || interaction.prompt?.timestamp || '');
    
    // Show the modal
    elements.interactionModal.show();
}

// Extract plain text from potentially HTML content
function extractTextContent(html) {
    if (!html) return '';
    
    // Create a temporary element
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Return text content
    return temp.textContent || temp.innerText || html;
}

// Update current activity based on recent logs
function updateCurrentActivity() {
    if (state.logs && state.logs.length > 0) {
        // Get the most recent logs (last 5)
        const recentLogs = state.logs.slice(-5);
        
        // Look for action logs first
        const actionLog = recentLogs.find(log => log.type === 'action');
        if (actionLog) {
            state.currentActivity = actionLog.message;
            elements.currentActivity.textContent = actionLog.message;
            return;
        }
        
        // Otherwise use the most recent log
        const latestLog = recentLogs[recentLogs.length - 1];
        state.currentActivity = `${latestLog.type}: ${latestLog.message}`;
        elements.currentActivity.textContent = state.currentActivity;
    }
}

// Update agent status indicator
function updateAgentStatus(status) {
    elements.agentStatus.className = status === 'online' 
        ? 'badge bg-success' 
        : 'badge bg-danger';
    
    elements.agentStatus.textContent = status === 'online' 
        ? 'Online' 
        : 'Offline';
}

// Update uptime display
function updateUptime(startTime) {
    try {
        const startDate = new Date(startTime);
        const now = new Date();
        const uptime = now - startDate;
        
        // Calculate uptime in a human-readable format
        const minutes = Math.floor(uptime / (1000 * 60));
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        let uptimeText = '';
        if (days > 0) {
            uptimeText = `${days}d ${hours % 24}h ${minutes % 60}m`;
        } else if (hours > 0) {
            uptimeText = `${hours}h ${minutes % 60}m`;
        } else {
            uptimeText = `${minutes}m`;
        }
        
        elements.agentUptime.textContent = uptimeText;
    } catch (error) {
        console.error('Error calculating uptime:', error);
        elements.agentUptime.textContent = 'Unknown';
    }
}

// Update last updated time
function updateLastUpdated() {
    const now = new Date();
    state.lastUpdated = now;
    elements.lastUpdated.textContent = now.toLocaleTimeString();
}

// Show error message
function showError(message) {
    console.error(message);
    alert(message);
}

// Format time for display
function formatTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    } catch (error) {
        return 'Invalid time';
    }
}

// Format date and time for display
function formatDateTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString();
    } catch (error) {
        return 'Invalid date';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);

