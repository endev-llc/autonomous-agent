// DOM Elements
const articlesListElement = document.getElementById('articles-list');
const resultsHeadingElement = document.getElementById('results-heading');
const searchInputElement = document.getElementById('search-input');
const searchButtonElement = document.getElementById('search-button');
const keywordFilterElement = document.getElementById('keyword-filter');
const scoreFilterElement = document.getElementById('score-filter');
const statsContentElement = document.getElementById('stats-content');
const articleTemplate = document.getElementById('article-template');

// State
let currentArticles = [];
let allKeywords = [];
let isSearchMode = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadRecentArticles();
    loadKeywords();
    loadStatistics();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Search button click
    searchButtonElement.addEventListener('click', () => {
        performSearch();
    });
    
    // Enter key in search input
    searchInputElement.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });
    
    // Filters change
    keywordFilterElement.addEventListener('change', filterArticles);
    scoreFilterElement.addEventListener('change', filterArticles);
}

// Load recent articles
async function loadRecentArticles() {
    try {
        const response = await fetch('/api/articles/recent');
        const articles = await response.json();
        
        currentArticles = articles;
        isSearchMode = false;
        resultsHeadingElement.textContent = 'Recent Articles';
        
        renderArticles(articles);
    } catch (error) {
        console.error('Error loading recent articles:', error);
        articlesListElement.innerHTML = '<p>Error loading articles. Please try again later.</p>';
    }
}

// Load all available keywords for filtering
async function loadKeywords() {
    try {
        const response = await fetch('/api/keywords');
        const keywords = await response.json();
        
        allKeywords = keywords;
        
        // Populate keyword filter dropdown
        keywordFilterElement.innerHTML = '<option value="">All keywords</option>';
        keywords.forEach(keyword => {
            const option = document.createElement('option');
            option.value = keyword;
            option.textContent = keyword;
            keywordFilterElement.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading keywords:', error);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        if (stats.length === 0) {
            statsContentElement.innerHTML = '<p>No statistics available yet.</p>';
            return;
        }
        
        // Get most recent stats
        const latestStats = stats[0];
        
        // Create stats cards
        statsContentElement.innerHTML = `
            <div class="stat-card">
                <h3>Articles Today</h3>
                <div class="value">${latestStats.articles_found || 0}</div>
            </div>
            <div class="stat-card">
                <h3>Processed Today</h3>
                <div class="value">${latestStats.articles_processed || 0}</div>
            </div>
            <div class="stat-card">
                <h3>Average Score</h3>
                <div class="value">${(latestStats.avg_score || 0).toFixed(1)}</div>
            </div>
            <div class="stat-card">
                <h3>Top Keywords</h3>
                <div class="keyword-list">
                    ${renderTopKeywords(latestStats.top_keywords || [])}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading statistics:', error);
        statsContentElement.innerHTML = '<p>Error loading statistics. Please try again later.</p>';
    }
}

// Render top keywords
function renderTopKeywords(keywords) {
    if (!keywords || keywords.length === 0) {
        return '<p>No keywords yet</p>';
    }
    
    return keywords.map(keyword => 
        `<span class="keyword-tag">${keyword}</span>`
    ).join('');
}

// Perform search
async function performSearch() {
    const query = searchInputElement.value.trim();
    
    if (!query) {
        loadRecentArticles();
        return;
    }
    
    try {
        articlesListElement.innerHTML = '<p>Searching...</p>';
        
        const response = await fetch(`/api/articles/search?q=${encodeURIComponent(query)}`);
        const articles = await response.json();
        
        currentArticles = articles;
        isSearchMode = true;
        
        if (articles.length === 0) {
            resultsHeadingElement.textContent = `No Results for "${query}"`;
            articlesListElement.innerHTML = '<p>No articles found matching your search.</p>';
        } else {
            resultsHeadingElement.textContent = `Search Results for "${query}"`;
            renderArticles(articles);
        }
    } catch (error) {
        console.error('Error searching articles:', error);
        articlesListElement.innerHTML = '<p>Error performing search. Please try again later.</p>';
    }
}

// Filter displayed articles
function filterArticles() {
    const keywordFilter = keywordFilterElement.value;
    const scoreFilter = parseFloat(scoreFilterElement.value);
    
    // Apply filters to current articles
    const filteredArticles = currentArticles.filter(article => {
        // Score filter
        if (article.score < scoreFilter) {
            return false;
        }
        
        // Keyword filter
        if (keywordFilter && Array.isArray(article.keywords)) {
            return article.keywords.includes(keywordFilter);
        }
        
        return true;
    });
    
    // Update heading
    if (isSearchMode) {
        const query = searchInputElement.value.trim();
        resultsHeadingElement.textContent = `Search Results for "${query}" (Filtered)`;
    } else {
        resultsHeadingElement.textContent = 'Recent Articles (Filtered)';
    }
    
    // Render filtered articles
    renderArticles(filteredArticles);
}

// Render articles to the DOM
function renderArticles(articles) {
    if (!articles || articles.length === 0) {
        articlesListElement.innerHTML = '<p>No articles found.</p>';
        return;
    }
    
    // Clear existing content
    articlesListElement.innerHTML = '';
    
    // Render each article
    articles.forEach(article => {
        // Clone template
        const articleElement = document.importNode(articleTemplate.content, true);
        
        // Set score badge
        const scoreBadge = articleElement.querySelector('.score-badge');
        scoreBadge.textContent = article.score?.toFixed(1) || '?';
        
        // Add score class
        if (article.score >= 9) {
            scoreBadge.classList.add('score-high');
        } else if (article.score >= 7) {
            scoreBadge.classList.add('score-medium');
        } else {
            scoreBadge.classList.add('score-low');
        }
        
        // Set article content
        articleElement.querySelector('.article-title').textContent = article.title;
        articleElement.querySelector('.article-source').textContent = article.source;
        articleElement.querySelector('.article-date').textContent = article.formatted_date || 'Unknown date';
        
        // Set summary - using innerHTML because it may contain markdown-generated HTML
        articleElement.querySelector('.article-summary').innerHTML = article.formatted_summary || article.summary || 'No summary available.';
        
        // Set keywords
        const keywordsContainer = articleElement.querySelector('.article-keywords');
        if (article.keywords && article.keywords.length > 0) {
            article.keywords.forEach(keyword => {
                const keywordTag = document.createElement('span');
                keywordTag.classList.add('keyword-tag');
                keywordTag.textContent = keyword;
                keywordsContainer.appendChild(keywordTag);
            });
        } else {
            keywordsContainer.innerHTML = '<span class="keyword-tag">No keywords</span>';
        }
        
        // Set link
        const linkElement = articleElement.querySelector('.article-link a');
        linkElement.href = article.url;
        
        // Add to the list
        articlesListElement.appendChild(articleElement);
    });
}
