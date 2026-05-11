document.addEventListener('DOMContentLoaded', () => {
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const chatWindow = document.getElementById('chat-window');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const sendMsgBtn = document.getElementById('send-msg-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Toggle chat window
    chatToggleBtn.addEventListener('click', () => {
        chatWindow.classList.remove('hidden');
        chatInput.focus();
    });

    closeChatBtn.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
    });

    // Send message logic
    const sendMessage = async () => {
        const text = chatInput.value.trim();
        if (!text) return;

        // Add user message to UI
        addMessage(text, 'user');
        chatInput.value = '';

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            // Send to backend
            const response = await fetch('http://localhost:5000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeElement(typingId);

            if (response.ok) {
                addMessage(data.answer, 'bot');
            } else {
                addMessage(data.error || "Sorry, I'm having trouble connecting right now.", 'bot');
            }
        } catch (error) {
            console.error("Error connecting to chat API:", error);
            removeElement(typingId);
            addMessage("Sorry, I'm unable to reach the server. Please ensure the backend is running and running on localhost:5000.", 'bot');
        }
    };

    // Event listeners for sending
    sendMsgBtn.addEventListener('click', sendMessage);
    
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Helper functions
    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        // simple parsing to handle line breaks for formatting
        contentDiv.innerHTML = text.replace(/\n/g, '<br>');
        
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.id = id;
        msgDiv.classList.add('message', 'bot');
        
        msgDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
});
