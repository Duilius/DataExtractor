// Toggle Chat Widget
const chatToggle = document.getElementById('chat-toggle');
const chatbot = document.getElementById('chatbot');
const closeChat = document.getElementById('close-chat');

chatToggle.addEventListener('click', () => {
    chatbot.style.display = 'flex';
    chatToggle.style.display = 'none';
});

closeChat.addEventListener('click', () => {
    chatbot.style.display = 'none';
    chatToggle.style.display = 'block';
});

// Handle Chat Messages
const sendBtn = document.getElementById('send-btn');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    displayMessage(userMessage, 'user');

    try {
        const response = await fetch('/chatbot/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: userMessage })
        });
        const data = await response.json();
        displayMessage(data.response, 'bot');
    } catch (error) {
        displayMessage("Hubo un error procesando tu solicitud.", 'bot');
    }

    chatInput.value = '';
}


function displayMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'message user' : 'message bot';
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Style Messages
const style = document.createElement('style');
style.innerHTML = `
.message {
    margin: 10px 0;
    padding: 10px;
    border-radius: 5px;
    max-width: 80%;
}

.message.user {
    background-color: #0078D7;
    color: white;
    align-self: flex-end;
}

.message.bot {
    background-color: #e5e5e5;
    align-self: flex-start;
}
`;
document.head.appendChild(style);
