/**
 * Frontend JavaScript for Course Materials RAG System
 * 
 * This script handles the chat interface, API communication, and UI updates
 * for the course Q&A system. It manages conversation sessions, displays
 * responses with source citations, and shows course statistics.
 */

// Configuration
const API_URL = '/api';  // Relative path for proxy compatibility

// Application State
let currentSessionId = null;  // Tracks conversation session for context

// DOM Element References (initialized after page load)
let chatMessages;    // Chat message container
let chatInput;       // User input field
let sendButton;      // Send message button
let totalCourses;    // Course count display
let courseTitles;    // Course list display

/**
 * Initialize application when DOM is ready
 * 
 * Sets up the chat interface, creates initial session,
 * and loads course statistics for display.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Cache DOM element references for performance
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    
    // Initialize application components
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

/**
 * Set up all event listeners for user interactions
 * 
 * Configures handlers for:
 * - Send button clicks
 * - Enter key in input field
 * - Suggested question buttons
 */
function setupEventListeners() {
    // Primary chat controls
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Quick-access suggested questions
    // Each button has a data-question attribute with preset query
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


/**
 * Send user message to the API and handle response
 * 
 * Workflow:
 * 1. Display user message in chat
 * 2. Show loading indicator
 * 3. Send query to backend API
 * 4. Display AI response with sources
 * 5. Handle errors gracefully
 * 
 * @async
 * @returns {Promise<void>}
 */
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;  // Ignore empty messages

    // Disable input during processing
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;

    // Display user message immediately for responsiveness
    addMessage(query, 'user');

    // Show loading animation while waiting for response
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        // Call RAG API with query and session context
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                session_id: currentSessionId  // Include for conversation continuity
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();
        
        // Store session ID for follow-up questions
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading indicator with actual response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // Display error message in chat
        loadingMessage.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    } finally {
        // Re-enable input for next message
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();  // Return focus for convenience
    }
}

/**
 * Create loading indicator element
 * 
 * Generates a message bubble with animated dots to show
 * the system is processing the query.
 * 
 * @returns {HTMLElement} Loading message DOM element
 */
function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

/**
 * Add a message to the chat display
 * 
 * Handles both user and assistant messages, with special support for:
 * - Markdown rendering in assistant responses
 * - Source citations in collapsible section
 * - Welcome message styling
 * 
 * @param {string} content - Message text content
 * @param {string} type - Message type: 'user' or 'assistant'
 * @param {Array<string>} sources - Optional source citations
 * @param {boolean} isWelcome - Whether this is the welcome message
 * @returns {number} Message ID for reference
 */
function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;
    
    // Render markdown for AI responses, escape HTML for user messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);
    
    let html = `<div class="message-content">${displayContent}</div>`;
    
    // Add collapsible sources section if citations provided
    if (sources && sources.length > 0) {
        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">${sources.join(', ')}</div>
            </details>
        `;
    }
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;  // Auto-scroll to latest
    
    return messageId;
}

/**
 * Escape HTML in user messages to prevent XSS
 * 
 * Converts special characters to HTML entities to safely
 * display user input without executing any embedded HTML/JS.
 * 
 * @param {string} text - Raw text to escape
 * @returns {string} HTML-safe text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Create a new chat session
 * 
 * Clears conversation history and displays welcome message.
 * Called on initial load and when user wants to start over.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function createNewSession() {
    currentSessionId = null;  // Reset session ID
    chatMessages.innerHTML = '';  // Clear chat history
    
    // Display welcome message with system capabilities
    addMessage(
        'Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?',
        'assistant',
        null,
        true  // Mark as welcome message for special styling
    );
}

/**
 * Load and display course statistics
 * 
 * Fetches metadata about indexed courses and updates the UI
 * to show available courses and total count.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await fetch(`${API_URL}/courses`);
        if (!response.ok) throw new Error('Failed to load course stats');
        
        const data = await response.json();
        console.log('Course data received:', data);
        
        // Display course count
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }
        
        // Display list of available courses
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                // Create a div for each course title
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }
        
    } catch (error) {
        console.error('Error loading course stats:', error);
        
        // Display fallback values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            courseTitles.innerHTML = '<span class="error">Failed to load courses</span>';
        }
    }
}