// Dashboard Configuration
const CONFIG = {
    apiBaseUrl: '/api',
    pollInterval: 5000,     // Poll for updates every 5 seconds
    logsPerPage: 15,        // Number of logs to display per page
    maxTimelineEntries: 10, // Max entries to show in timeline
    maxInteractions: 50     // Max interactions to store
};

// Application State
const state = {
    memory: null,
    logs: [],
    interactions: [],
    agentInfo: null,
    lastUpdated: null,
    currentActivity: "Initializing",
    currentStage: "Initialize",
    // Pagination state
    logsPage: 1,
    totalLogsPages: 1,
    currentInteractionIndex: 0,
    // Filtering
    logFilter: 'all'
};

// DOM Elements
const elements = {
    // Agent Info
    agentStatus: document.getElementById('agent-status-indicator'),
    agentName: document.getElementById('agent-name'),
    agentGoal: document.getElementById('agent-goal'),
    agentModel: document.getElementById('agent-model'),
    agentUptime: document.getElementById('agent-uptime'),
    agentActionsCount: document.getElementById('agent-actions-count'),
    lastUpdated: document.getElementById('last-updated'),
    footerLastUpdated: document.getElementById('footer-last-updated'),
    
    // Current Status
    currentActivity: document.getElementById('current-activity'),
    progressSteps: document.querySelectorAll('.progress-step'),
    
    // Timeline
    timelineContainer: document.getElementById('timeline-container'),
    refreshTimeline: document.getElementById('refresh-timeline'),
    
    // Interactions
    interactionPrompt: document.getElementById('interaction-prompt'),
    interactionResponse: document.getElementById('interaction-response'),
    interactionTimestamp: document.getElementById('interaction-timestamp'),
    interactionPageInfo: document.getElementById('interaction-page-info'),
    prevInteraction: document.getElementById('prev-interaction'),
    nextInteraction: document.getElementById('next-interaction'),
    
    // Logs
    logsTable: document.getElementById('logs-table'),
    logsBody: document.getElementById('logs-body'),
    logsPageInfo: document.getElementById('logs-page-info'),
    clearLogs: document.getElementById('clear-logs'),
    logFilters: document.querySelectorAll('.filter-log'),
    logsFirstPage: document.getElementById('logs-first-page'),
    logsPrevPage: document.getElementById('logs-prev-page'),
    logsNextPage: document.getElementById('logs-next-page'),
    logsLastPage: document.getElementById('logs-last-page'),
    
    // Memory
    memoryDisplay: document.getElementById('memory-display'),
    refreshMemory: document.getElementById('refresh-memory'),
    
    // Tabs
    mainTabs: document.querySelectorAll('[data-bs-toggle="tab"]')
};

// -------------- Initialization and Polling --------------

// Initialize the dashboard
function initDashboard() {
    // Set up event listeners
    setupEventListeners();
    
    // Start polling for updates
    fetchInitialData();
    setInterval(pollForUpdates, CONFIG.pollInterval);
    
    // Update time
    updateLastUpdated();
}

// Set up event listeners
function setupEventListeners() {
    // Timeline
    elements.refreshTimeline.addEventListener('click', refreshTimeline);
    
    // Interactions navigation
    elements.prevInteraction.addEventListener('click', showPreviousInteraction);
    elements.nextInteraction.addEventListener('click', showNextInteraction);
    
    // Logs
    elements.clearLogs.addEventListener('click', clearLogs);
    elements.logFilters.forEach(filter => {
        filter.addEventListener('click', () => filterLogs(filter.dataset.filter));
    });
    
    // Logs pagination
    elements.logsFirstPage.addEventListener('click', () => goToLogsPage(1));
    elements.logsPrevPage.addEventListener('click', () => goToLogsPage(state.logsPage - 1));
    elements.logsNextPage.addEventListener('click', () => goToLogsPage(state.logsPage + 1));
    elements.logsLastPage.addEventListener('click', () => goToLogsPage(state.totalLogsPages));
    
    // Memory
    elements.refreshMemory.addEventListener('click', refreshMemory);
    
    // Tab change events
    elements.mainTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            if (e.target.id === 'memory-tab') {
                refreshMemory();
            } else if (e.target.id === 'timeline-tab') {
                refreshTimeline();
            }
        });
    });
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
        
        // Fetch interactions history
        await fetchInteractionsHistory();
        
        // Generate timeline
        generateTimeline();
        
        // Set agent status to online
        updateAgentStatus('online');
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
        const newLogs = await fetchNewLogs();
        if (newLogs && newLogs.length > 0) {
            appendLogs(newLogs);
            updateTimeline();
        }
        
        // Check for latest interaction
        const latestInteraction = await fetchLatestInteraction();
        if (latestInteraction && (latestInteraction.prompt || latestInteraction.response)) {
            updateInteractions(latestInteraction);
        }
        
        // Check current activity and stage
        updateCurrentStatus();
        
        // Update last updated time
        updateLastUpdated();
        
        // Set agent status to online
        updateAgentStatus('online');
    } catch (error) {
        console.error('Error polling for updates:', error);
        updateAgentStatus('offline');
    }
}

// -------------- API Calls --------------

// Fetch agent information
async function fetchAgentInfo() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/agent-info`);
        if (!response.ok) {
            throw new Error(`Error fetching agent info: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching agent info:', error);
        return null;
    }
}

// Fetch agent memory
async function fetchMemory() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/memory`);
        if (!response.ok) {
            throw new Error(`Error fetching memory: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching memory:', error);
        return { content: "Error loading memory" };
    }
}

// Fetch all logs
async function fetchLogs(limit = 1000) {
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

// Fetch new logs since last update
async function fetchNewLogs() {
    if (!state.lastUpdated) return [];
    
    try {
        const timestamp = state.lastUpdated.toISOString();
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

// Fetch the latest interaction
async function fetchLatestInteraction() {
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

// -------------- Data Processing --------------

// Build a history of all interactions from the logs
async function fetchInteractionsHistory() {
    try {
        // Get all logs
        const allLogs = await fetchLogs(1000);
        
        // Group prompts and responses
        let interactions = [];
        let currentPrompt = null;
        
        // Sort logs by timestamp
        allLogs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        for (const log of allLogs) {
            if (log.type === 'prompt') {
                // Start a new interaction
                currentPrompt = {
                    timestamp: log.timestamp,
                    content: log.message
                };
            } else if (log.type === 'response' && currentPrompt) {
                // Complete the interaction
                interactions.push({
                    prompt: currentPrompt,
                    response: {
                        timestamp: log.timestamp,
                        content: log.message
                    }
                });
                currentPrompt = null;
            }
        }
        
        // Limit to max interactions
        if (interactions.length > CONFIG.maxInteractions) {
            interactions = interactions.slice(-CONFIG.maxInteractions);
        }
        
        state.interactions = interactions;
        updateInteractionControls();
        showLatestInteraction();
        
        return interactions;
    } catch (error) {
        console.error('Error building interactions history:', error);
        return [];
    }
}

// Create a summarized timeline from the logs
function generateTimeline() {
    const timelineGroups = [];
    let currentGroup = null;
    
    // Helper function to add a new group
    function startNewGroup(log) {
        return {
            startTime: log.timestamp,
            endTime: log.timestamp,
            activity: determineActivity(log),
            stage: determineStage(log),
            logType: log.type,
            details: [log.message],
            count: 1
        };
    }
    
    // Process logs to create timeline groups
    for (const log of state.logs) {
        // Skip non-significant logs
        if (!isSignificantForTimeline(log)) continue;
        
        if (!currentGroup || !areLogsRelated(currentGroup, log)) {
            // Start a new group if needed
            if (currentGroup) {
                timelineGroups.push(currentGroup);
            }
            currentGroup = startNewGroup(log);
        } else {
            // Update the current group
            currentGroup.endTime = log.timestamp;
            currentGroup.details.push(log.message);
            currentGroup.count++;
        }
    }
    
    // Add the last group
    if (currentGroup) {
        timelineGroups.push(currentGroup);
    }
    
    // Limit timeline entries
    const limitedTimeline = timelineGroups.slice(-CONFIG.maxTimelineEntries);
    
    // Update the timeline UI
    renderTimeline(limitedTimeline);
    
    return limitedTimeline;
}

// Determine if a log is significant for the timeline
function isSignificantForTimeline(log) {
    // Include action, reflection, and error logs
    return ['action', 'reflection', 'error'].includes(log.type) || 
           // Include important info logs about activity
           (log.type === 'info' && 
            (log.message.includes('initialized') || 
             log.message.includes('strategy') || 
             log.message.includes('completed')));
}

// Determine if two logs should be grouped together
function areLogsRelated(group, log) {
    // Group by log type and time proximity (within 5 minutes)
    const timeThreshold = 5 * 60 * 1000; // 5 minutes
    const timeA = new Date(group.endTime);
    const timeB = new Date(log.timestamp);
    const timeDiff = Math.abs(timeB - timeA);
    
    return group.logType === log.type && timeDiff < timeThreshold;
}

// Determine the activity description from a log
function determineActivity(log) {
    if (log.type === 'action') {
        if (log.message.includes('initialized')) return 'Initialization';
        if (log.message.includes('research')) return 'Research';
        if (log.message.includes('analyz')) return 'Analysis';
        if (log.message.includes('categori')) return 'Categorization';
        if (log.message.includes('develop')) return 'Development';
        return 'Activity';
    } else if (log.type === 'reflection') {
        return 'Reflection';
    } else if (log.type === 'error') {
        return 'Error';
    } else {
        return 'Activity';
    }
}

// Determine the current stage from a log
function determineStage(log) {
    const message = log.message.toLowerCase();
    
    if (message.includes('initializ') || message.includes('starting')) {
        return 'Initialize';
    } else if (message.includes('research') || message.includes('review') || message.includes('literature')) {
        return 'Research';
    } else if (message.includes('analyz') || message.includes('evaluat')) {
        return 'Analyze';
    } else if (message.includes('develop') || message.includes('implement') || message.includes('build')) {
        return 'Develop';
    } else if (message.includes('finaliz') || message.includes('complet') || message.includes('finish')) {
        return 'Finalize';
    }
    
    return state.currentStage; // Keep current stage if no change detected
}

// Update the current status based on recent logs
function updateCurrentStatus() {
    if (state.logs.length === 0) return;
    
    // Look at the most recent logs
    const recentLogs = state.logs.slice(-10);
    
    // Try to determine current activity
    for (let i = recentLogs.length - 1; i >= 0; i--) {
        const log = recentLogs[i];
        if (log.type === 'action' || log.type === 'reflection') {
            state.currentActivity = log.message;
            elements.currentActivity.textContent = log.message;
            break;
        }
    }
    
    // Try to determine current stage
    for (let i = recentLogs.length - 1; i >= 0; i--) {
        const log = recentLogs[i];
        const newStage = determineStage(log);
        if (newStage !== state.currentStage) {
            state.currentStage = newStage;
            updateProgressTracker(state.currentStage);
            break;
        }
    }
}

// Update the timeline when new logs arrive
function updateTimeline() {
    generateTimeline();
}

// -------------- UI Updates --------------

// Update agent info
function updateAgentInfo(info) {
    if (!info) return;
    
    state.agentInfo = info;
    elements.agentName.textContent = info.name || 'Unknown';
    elements.agentGoal.textContent = info.goal || 'No goal specified';
    elements.agentModel.textContent = info.model || 'Unknown model';
    
    // Calculate uptime
    if (info.startTime) {
        const startTime = new Date(info.startTime);
        updateUptime(startTime);
        // Set interval to update uptime every minute
        setInterval(() => updateUptime(startTime), 60000);
    }
}

// Update uptime display
function updateUptime(startTime) {
    const now = new Date();
    const diff = now - startTime;
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    let uptimeText = '';
    if (days > 0) uptimeText += `${days}d `;
    if (hours > 0 || days > 0) uptimeText += `${hours}h `;
    uptimeText += `${minutes}m`;
    
    elements.agentUptime.textContent = uptimeText;
}

// Update agent status indicator
function updateAgentStatus(status) {
    elements.agentStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    elements.agentStatus.className = `badge bg-${status === 'online' ? 'success' : 'danger'}`;
}

// Update the memory display
function updateMemory(memory) {
    if (!memory || !memory.content) return;
    
    state.memory = memory;
    
    // Convert markdown to HTML for better formatting
    try {
        const htmlContent = marked.parse(memory.content);
        elements.memoryDisplay.innerHTML = htmlContent;
    } catch (error) {
        console.error('Error parsing memory markdown:', error);
        elements.memoryDisplay.textContent = memory.content;
    }
}

// Update logs data and UI
function updateLogs(logs) {
    if (!logs || !logs.length) return;
    
    console.log(`Received ${logs.length} logs from the server.`);
    
    // Replace existing logs
    state.logs = logs;
    
    // Update action count
    updateActionCount();
    
    // Render logs with current filter and page
    renderLogs();
}

// Append new logs
function appendLogs(newLogs) {
    if (!newLogs || !newLogs.length) return;
    
    // Add new logs to the state
    state.logs = [...state.logs, ...newLogs];
    
    // Update action count
    updateActionCount();
    
    // Render the logs
    renderLogs();
}

// Update interactions
function updateInteractions(interaction) {
    if (!interaction) return;
    
    // Process the interaction object
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
    
    // Only add if we have both prompt and response
    if (prompt && response) {
        const newInteraction = {
            prompt: {
                content: prompt,
                timestamp: timestamp || new Date().toISOString()
            },
            response: {
                content: response,
                timestamp: new Date().toISOString()
            }
        };
        
        // Add to interactions if it's new
        if (!hasInteraction(newInteraction)) {
            state.interactions.push(newInteraction);
            
            // Limit to max interactions
            if (state.interactions.length > CONFIG.maxInteractions) {
                state.interactions = state.interactions.slice(-CONFIG.maxInteractions);
            }
            
            // Show the latest interaction
            state.currentInteractionIndex = state.interactions.length - 1;
            showCurrentInteraction();
            updateInteractionControls();
        }
    }
}

// Check if an interaction already exists in the state
function hasInteraction(newInteraction) {
    return state.interactions.some(interaction => {
        return interaction.prompt.content === newInteraction.prompt.content &&
               interaction.response.content === newInteraction.response.content;
    });
}

// Update the progress tracker
function updateProgressTracker(stage) {
    elements.progressSteps.forEach(step => {
        const stepStage = step.dataset.stage;
        step.classList.remove('active', 'completed');
        
        if (stepStage === stage) {
            step.classList.add('active');
        } else {
            // Check if this step should be marked as completed
            const stages = ['Initialize', 'Research', 'Analyze', 'Develop', 'Finalize'];
            const currentIndex = stages.indexOf(stage);
            const stepIndex = stages.indexOf(stepStage);
            
            if (stepIndex < currentIndex) {
                step.classList.add('completed');
            }
        }
    });
}

// Update the last updated timestamp
function updateLastUpdated() {
    state.lastUpdated = new Date();
    const formattedTime = formatDateTime(state.lastUpdated);
    elements.lastUpdated.textContent = formattedTime;
    elements.footerLastUpdated.textContent = formattedTime;
}

// Update action count
function updateActionCount() {
    const actionCount = state.logs.filter(log => log.type === 'action').length;
    elements.agentActionsCount.textContent = actionCount;
}

// -------------- Rendering Functions --------------

// Render logs with current filter and pagination
function renderLogs() {
    // Get filtered logs
    const filteredLogs = state.logFilter === 'all' 
        ? state.logs 
        : state.logs.filter(log => log.type === state.logFilter);
    
    console.log(`Rendering logs: ${filteredLogs.length} filtered logs out of ${state.logs.length} total logs`);
    
    // Update pagination info
    state.totalLogsPages = Math.max(1, Math.ceil(filteredLogs.length / CONFIG.logsPerPage));
    if (state.logsPage > state.totalLogsPages) {
        state.logsPage = Math.max(1, state.totalLogsPages);
    }
    
    // Get logs for current page
    const startIndex = (state.logsPage - 1) * CONFIG.logsPerPage;
    const endIndex = startIndex + CONFIG.logsPerPage;
    const pageData = filteredLogs.slice(startIndex, endIndex);
    
    console.log(`Page ${state.logsPage}/${state.totalLogsPages}: Showing logs ${startIndex+1}-${Math.min(endIndex, filteredLogs.length)} of ${filteredLogs.length}`);
    
    // Clear table
    elements.logsBody.innerHTML = '';
    
    // Add logs to table
    if (pageData.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="3" class="text-center">No logs available</td>';
        elements.logsBody.appendChild(row);
    } else {
        pageData.forEach(log => {
            const row = document.createElement('tr');
            
            const timeCell = document.createElement('td');
            timeCell.textContent = formatTime(log.timestamp);
            
            const typeCell = document.createElement('td');
            const typeSpan = document.createElement('span');
            typeSpan.textContent = log.type.toUpperCase();
            typeSpan.className = `badge badge-${log.type}`;
            typeCell.appendChild(typeSpan);
            
            const messageCell = document.createElement('td');
            messageCell.textContent = log.message;
            
            row.appendChild(timeCell);
            row.appendChild(typeCell);
            row.appendChild(messageCell);
            
            elements.logsBody.appendChild(row);
        });
    }
    
    // Update pagination buttons
    updateLogsPaginationControls();
}

// Update the interaction controls
function updateInteractionControls() {
    // Update interaction counter
    elements.interactionPageInfo.textContent = state.interactions.length > 0
        ? `Interaction ${state.currentInteractionIndex + 1} of ${state.interactions.length}`
        : 'No interactions';
    
    // Update button states
    elements.prevInteraction.disabled = state.currentInteractionIndex <= 0;
    elements.nextInteraction.disabled = state.currentInteractionIndex >= state.interactions.length - 1;
}

// Show the current interaction
function showCurrentInteraction() {
    if (state.interactions.length === 0) {
        elements.interactionPrompt.textContent = 'No prompt available';
        elements.interactionResponse.innerHTML = 'No response available';
        elements.interactionTimestamp.textContent = 'No timestamp available';
        return;
    }
    
    const interaction = state.interactions[state.currentInteractionIndex];
    
    // Update prompt
    elements.interactionPrompt.textContent = interaction.prompt.content || 'No prompt content';
    
    // Update response (with markdown formatting)
    try {
        elements.interactionResponse.innerHTML = marked.parse(interaction.response.content || 'No response content');
    } catch (error) {
        elements.interactionResponse.textContent = interaction.response.content || 'No response content';
    }
    
    // Update timestamp
    elements.interactionTimestamp.textContent = `Interaction at ${formatDateTime(interaction.prompt.timestamp)}`;
    
    // Apply syntax highlighting
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Show the latest interaction
function showLatestInteraction() {
    if (state.interactions.length > 0) {
        state.currentInteractionIndex = state.interactions.length - 1;
        showCurrentInteraction();
        updateInteractionControls();
    }
}

// Render the timeline
function renderTimeline(timelineGroups) {
    elements.timelineContainer.innerHTML = '';
    
    if (!timelineGroups || timelineGroups.length === 0) {
        elements.timelineContainer.innerHTML = '<div class="text-center p-4">No timeline data available</div>';
        return;
    }
    
    timelineGroups.forEach(group => {
        const entry = document.createElement('div');
        entry.className = 'timeline-entry';
        
        const icon = document.createElement('div');
        icon.className = `timeline-icon ${group.logType}`;
        
        const content = document.createElement('div');
        content.className = 'timeline-content';
        
        const time = document.createElement('div');
        time.className = 'timeline-time';
        time.textContent = formatDateTime(group.startTime);
        
        const title = document.createElement('div');
        title.className = 'timeline-title';
        title.textContent = group.activity;
        
        const details = document.createElement('div');
        details.className = 'timeline-details';
        details.textContent = group.details[0];
        if (group.count > 1) {
            details.textContent += ` (and ${group.count - 1} more actions)`;
        }
        
        content.appendChild(time);
        content.appendChild(title);
        content.appendChild(details);
        
        entry.appendChild(icon);
        entry.appendChild(content);
        
        elements.timelineContainer.appendChild(entry);
    });
}

// Update the logs pagination controls
function updateLogsPaginationControls() {
    elements.logsPageInfo.textContent = `Page ${state.logsPage} of ${state.totalLogsPages}`;
    
    elements.logsFirstPage.disabled = state.logsPage <= 1;
    elements.logsPrevPage.disabled = state.logsPage <= 1;
    elements.logsNextPage.disabled = state.logsPage >= state.totalLogsPages;
    elements.logsLastPage.disabled = state.logsPage >= state.totalLogsPages;
}

// -------------- Event Handlers --------------

// Show previous interaction
function showPreviousInteraction() {
    if (state.currentInteractionIndex > 0) {
        state.currentInteractionIndex--;
        showCurrentInteraction();
        updateInteractionControls();
    }
}

// Show next interaction
function showNextInteraction() {
    if (state.currentInteractionIndex < state.interactions.length - 1) {
        state.currentInteractionIndex++;
        showCurrentInteraction();
        updateInteractionControls();
    }
}

// Clear logs
function clearLogs() {
    if (confirm('Are you sure you want to clear the logs display? This does not delete the logs from the agent.')) {
        state.logs = [];
        renderLogs();
    }
}

// Filter logs by type
function filterLogs(filterType) {
    state.logFilter = filterType;
    state.logsPage = 1;
    
    // Update filter buttons
    elements.logFilters.forEach(filter => {
        filter.classList.toggle('active', filter.dataset.filter === filterType);
    });
    
    console.log(`Filtering logs by: ${filterType}. Total logs: ${state.logs.length}`);
    renderLogs();
}

// Go to a specific logs page
function goToLogsPage(page) {
    if (page < 1 || page > state.totalLogsPages) return;
    
    state.logsPage = page;
    renderLogs();
}

// Refresh the timeline
function refreshTimeline() {
    generateTimeline();
}

// Refresh memory
function refreshMemory() {
    fetchMemory().then(memory => {
        updateMemory(memory);
    });
}

// Show an error message
function showError(message) {
    console.error(message);
    // Add to logs if available
    if (state.logs) {
        const errorLog = {
            type: 'error',
            message: message,
            timestamp: new Date().toISOString()
        };
        state.logs.push(errorLog);
        renderLogs();
    }
}

// -------------- Helper Functions --------------

// Format timestamp to date and time
function formatDateTime(timestamp) {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Format timestamp to just time
function formatTime(timestamp) {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initDashboard);
