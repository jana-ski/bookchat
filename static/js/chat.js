class ChatManager {
    constructor(options = {}) {
        this.messageInput = document.getElementById(options.inputId || 'message-input');
        this.sendButton = document.getElementById(options.sendButtonId || 'send-button');
        this.messageArea = document.getElementById(options.messageAreaId || 'message-area');
        this.errorElement = document.getElementById(options.errorId || 'error');
        
        this.endpoints = {
            send: options.sendEndpoint || '/chat',
            fetch: options.fetchEndpoint || '/messages'
        };
        
        this.updateInterval = options.updateInterval || 5000; // 5 seconds
        this.lastMessageTimestamp = null;
        
        this.setupEventListeners();
        this.startPeriodicFetch();
    }
    
    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Input validation
        this.messageInput.addEventListener('input', () => {
            const isEmpty = !this.messageInput.value.trim();
            this.sendButton.disabled = isEmpty;
        });
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        try {
            this.sendButton.disabled = true;
            const response = await fetch(this.endpoints.send, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.status === 'error') {
                throw new Error(data.message);
            }
            
            // Add message to display
            this.addMessage({
                message,
                timestamp: new Date().toISOString(),
                github_url: data.github_url
            });
            
            this.messageInput.value = '';
            this.errorElement.textContent = '';
            
        } catch (error) {
            this.showError(`Error sending message: ${error.message}`);
        } finally {
            this.sendButton.disabled = false;
        }
    }
    
    async fetchMessages() {
        try {
            const response = await fetch(this.endpoints.fetch);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.messages && data.messages.length > 0) {
                // Check if we have new messages
                const latestTimestamp = data.messages[0].timestamp;
                if (latestTimestamp !== this.lastMessageTimestamp) {
                    this.updateMessages(data.messages);
                    this.lastMessageTimestamp = latestTimestamp;
                }
            }
        } catch (error) {
            this.showError(`Error fetching messages: ${error.message}`);
        }
    }
    
    updateMessages(messages) {
        // Clear existing messages if this is the first load
        if (!this.lastMessageTimestamp) {
            this.messageArea.innerHTML = '';
        }
        
        // Add only new messages
        messages.forEach(msg => {
            if (!this.messageExists(msg.id)) {
                this.addMessage(msg);
            }
        });
    }
    
    messageExists(id) {
        return !!document.querySelector(`[data-message-id="${id}"]`);
    }
    
    addMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        if (message.id) {
            messageDiv.setAttribute('data-message-id', message.id);
        }
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date(message.timestamp).toLocaleString();
        
        const content = document.createElement('div');
        content.className = 'content';
        content.textContent = message.message;
        
        messageDiv.appendChild(timestamp);
        messageDiv.appendChild(content);
        
        if (message.github_url) {
            const link = document.createElement('a');
            link.href = message.github_url;
            link.target = '_blank';
            link.textContent = 'View on GitHub';
            link.className = 'github-link';
            messageDiv.appendChild(link);
        }
        
        this.messageArea.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        this.messageArea.scrollTop = this.messageArea.scrollHeight;
    }
    
    showError(message) {
        this.errorElement.textContent = message;
        setTimeout(() => {
            this.errorElement.textContent = '';
        }, 5000);
    }
    
    startPeriodicFetch() {
        // Fetch immediately
        this.fetchMessages();
        
        // Then fetch periodically
        setInterval(() => this.fetchMessages(), this.updateInterval);
    }
}

// Initialize chat when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatManager({
        updateInterval: 3000, // Check for new messages every 3 seconds
    });
});
