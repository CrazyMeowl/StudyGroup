const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatSubmit = document.getElementById('chat-submit');
const chatMessages = document.getElementById('chat-messages');
const chatBox = document.getElementById('chat-box');
const expandButton = document.getElementById('expand-button');
const clearButton = document.getElementById('clear-button');

const hideButton = document.getElementById('hide-chat-btn');

chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        if (!e.shiftKey) {
            e.preventDefault(); // Prevent newline
            chatForm.requestSubmit(); // Submit the form
        }
        // If Shift+Enter, do nothing – browser will insert newline
    }
});
// Handle the form submission (sending the chat message)
chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    chatInput.disabled = true;
    chatSubmit.disabled = true;

    // Add the user's message to the chat
    chatMessages.innerHTML += `<div class="chat-bubble user"><strong>You:</strong><br>${message.replace(/\n/g, "<br/>")}</div>`;

    // Clear the input field
    chatInput.value = "";

    try {
        const response = await fetch("/accounts/chat/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": '{{ csrf_token }}',
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();
        // Add AI's response to the chat
        chatMessages.innerHTML += `<div class="chat-bubble ai"><strong>AI:</strong><br>${data.reply.replace(/\n/g, "<br/>")}</div>`;

        // Scroll to the latest message
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        chatMessages.innerHTML += `<p class="text-danger"><strong>Error:</strong> Could not contact AI assistant.</p>`;
    }

    // Re-enable input and button
    chatInput.disabled = false;
    chatSubmit.disabled = false;
    chatInput.focus();
});

// Hide chatbox and show expand button
hideButton.addEventListener('click', () => {
    chatBox.style.display = 'none';
    expandButton.style.display = 'flex';
});

// Expand chatbox
function expandChat() {
    chatBox.style.display = 'flex';
    expandButton.style.display = 'none';
}


function clearChat() {
    const chatMessages = document.getElementById('chat-messages');

    // Clear the chat UI
    chatMessages.innerHTML = '';

    // Clear server-side session or TinyDB history (only if this endpoint is still valid)
    fetch('/accounts/clear_chat/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        },
    });
}

function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}
