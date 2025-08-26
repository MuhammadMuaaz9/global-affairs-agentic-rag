// Firebase configuration and initialization
const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  storageBucket: "",
  messagingSenderId: "",
  appId: ""
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Auth state variables
let currentUser = null;

// Auth state listener
auth.onAuthStateChanged((user) => {
    if (user) {
        currentUser = user;
        console.log("User logged in:", user.email);
        startNewChat();
        loadSidebarChats();
        show_view('.new-chat-view');
    } else {
        currentUser = null;
        showAuthModal();
    }
});

// Auth functions
function showAuthModal() {
    // Create auth modal HTML
    const authModalHTML = `
        <div id="auth-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 30px; border-radius: 10px; width: 300px;">
                <h2 id="auth-title">Login</h2>
                <input type="email" id="auth-email" placeholder="Email" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;">
                <input type="password" id="auth-password" placeholder="Password" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;">
                <button id="auth-submit" style="width:100%;padding:10px;background:#007bff;color:white;border:none;border-radius:5px;cursor:pointer;display:flex;justify-content:center;align-items:center;">Login</button>
                <p style="text-align: center; margin: 10px 0;">
                    <span id="auth-switch-text">Don't have an account?</span>
                    <a href="#" id="auth-switch" style="color: #007bff;">Sign up</a>
                </p>
                <div id="auth-error" style="color: red; margin-top: 10px; display: none;"></div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', authModalHTML);
    
    let isLogin = true;
    
    document.getElementById('auth-switch').addEventListener('click', (e) => {
        e.preventDefault();
        isLogin = !isLogin;
        const title = document.getElementById('auth-title');
        const submit = document.getElementById('auth-submit');
        const switchText = document.getElementById('auth-switch-text');
        const switchLink = document.getElementById('auth-switch');
        
        if (isLogin) {
            title.textContent = 'Login';
            submit.textContent = 'Login';
            switchText.textContent = "Don't have an account?";
            switchLink.textContent = 'Sign up';
        } else {
            title.textContent = 'Sign Up';
            submit.textContent = 'Sign Up';
            switchText.textContent = 'Already have an account?';
            switchLink.textContent = 'Login';
        }
    });
    
    document.getElementById('auth-submit').addEventListener('click', async () => {
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        const errorDiv = document.getElementById('auth-error');
        
        try {
            if (isLogin) {
                await auth.signInWithEmailAndPassword(email, password);
            } else {
                await auth.createUserWithEmailAndPassword(email, password);
            }
            document.getElementById('auth-modal').remove();
        } catch (error) {
            errorDiv.style.display = 'block';
            errorDiv.textContent = error.message;
        }
    });
}

function logout() {
    auth.signOut();
}


// ==============================================================

// Global variables
let ws = null;
let fullMessage = "";
let currentAssistantMessage = null;
let currentThreadId = Date.now().toString();

// DOM elements
const sidebar = document.querySelector("#sidebar");
const hide_sidebar = document.querySelector(".hide-sidebar");
const new_chat_button = document.querySelector(".new-chat");
const message_box = document.querySelector("#message");
const sendButton = document.querySelector('.send-button');

// WebSocket creation
function createWebSocket(threadId) {

    if (!currentUser) {
        console.error("No user logged in");
        return;
    }

    if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
        }
    }
    
    const userThreadId = `${currentUser.uid}_${threadId}`;
    ws = new WebSocket(`ws://localhost:8002/ws/${userThreadId}/${currentUser.uid}`);
    
    ws.onopen = function() {
        console.log(`WebSocket connected to thread: ${threadId}`);
    };
    
    ws.onmessage = function(event) {
        fullMessage += event.data;
        if (currentAssistantMessage) {
            const content = currentAssistantMessage.querySelector('.content p');
            content.innerHTML = makeLinksClickable(fullMessage);
            scrollToBottom();
        }
    };
    
    ws.onclose = function(event) {
        console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
        ws = null;
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// Message sending with proper validation
function sendMessage() {
    const message = message_box.value.trim();
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) {
        console.log('Cannot send: no message or WebSocket not ready');
        return;
    }

    // Handle new chat creation
    const newChatView = document.querySelector('.new-chat-view');
    const isOnHomePage = newChatView && newChatView.style.display !== 'none';
    
    if (isOnHomePage) {
        //  add to sidebar with CURRENT threadId
        addChatToSidebar(currentThreadId, message);
    }
    
    show_view('.conversation-view');
    addUserMessage(message);
    addAssistantMessage();
    updateChatTitle(message);
    
    fullMessage = "";
    ws.send(message);
    
    message_box.value = '';
    message_box.style.height = "auto";
}

function switchToChat(threadId) {
    if (currentThreadId === threadId) return;
    
    document.querySelectorAll('.conversations li.active').forEach(item => {
        item.classList.remove('active');
    });
    
    const chatElement = document.querySelector(`li[data-thread-id="${threadId}"]`);
    if (chatElement) {
        chatElement.classList.add('active');
    }
    
    currentThreadId = threadId;
    createWebSocket(threadId);
    show_view(".conversation-view");
    loadChatHistory(threadId);
}

function startNewChat() {
    const newThreadId = Date.now().toString();
    currentThreadId = newThreadId;
    createWebSocket(newThreadId);
    return newThreadId;
}

// Helper functions
function show_view(view_selector) {
    document.querySelectorAll(".view").forEach(view => {
        view.style.display = "none";
    });
    document.querySelector(view_selector).style.display = "flex";
}

function makeLinksClickable(text) {
    const urlRegex = /(https?:\/\/[^\s\)]+)/g;
    return text.replace(urlRegex, '<a href="$1" target="_blank" style="color: blue; text-decoration: underline;">$1</a>');
}

function scrollToBottom() {
    const conversationView = document.querySelector('.conversation-view');
    conversationView.scrollTop = conversationView.scrollHeight;
}

function addUserMessage(message) {
    const conversationView = document.querySelector('.conversation-view');
    const userMessageHTML = `
        <div class="user message">
            <div class="identity"><i class="user-icon">You</i></div>
            <div class="content"><p>${message}</p></div>
        </div>
    `;
    conversationView.insertAdjacentHTML('beforeend', userMessageHTML);
}

function addAssistantMessage() {
    const conversationView = document.querySelector('.conversation-view');
    const assistantMessageHTML = `
        <div class="assistant message">
            <div class="identity"><i class="gpt user-icon">Ai</i></div>
            <div class="content"><p></p></div>
        </div>
    `;
    conversationView.insertAdjacentHTML('beforeend', assistantMessageHTML);
    
    const messages = conversationView.querySelectorAll('.assistant.message');
    currentAssistantMessage = messages[messages.length - 1];
}

function addAssistantMessageComplete(content) {
    const conversationView = document.querySelector('.conversation-view');
    const assistantMessageHTML = `
        <div class="assistant message">
            <div class="identity">
                <i class="gpt user-icon">Ai</i>
            </div>
            <div class="content">
                <p>${makeLinksClickable(content)}</p>
            </div>
        </div>
    `;
    conversationView.insertAdjacentHTML('beforeend', assistantMessageHTML);
}

function clearConversation() {
    const conversationView = document.querySelector('.conversation-view');
    conversationView.innerHTML = '';
    
    fullMessage = "";
    currentAssistantMessage = null;
}

function updateChatTitle(firstMessage) {
    const activeChat = document.querySelector('.conversations li.active .conversation-button');
    if (activeChat && activeChat.textContent.includes('New Chat')) {
        const title = firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
        activeChat.innerHTML = `<i class="fa fa-message fa-regular"></i> ${title}`;
    }
}

function addChatToSidebar(threadId, title = "New Chat") {
    const conversationsList = document.querySelector('.conversations');
    const todayGroup = conversationsList.querySelector('li.grouping');
    
    document.querySelectorAll('.conversations li.active').forEach(item => {
        item.classList.remove('active');
    });

    const displayTitle = title.length > 30 ? title.substring(0, 30) + '...' : title;
    
    const newChatHTML = `
        <li class="active" data-thread-id="${threadId}">
            <button class="conversation-button"><i class="fa fa-message fa-regular"></i> ${displayTitle}</button>
            <div class="fade"></div>
            <div class="edit-buttons">
                <button><i class="fa fa-edit"></i></button>
                <button><i class="fa fa-trash"></i></button>
            </div>
        </li>
    `;
    
    todayGroup.insertAdjacentHTML('afterend', newChatHTML);
    
    // Add event listener to new chat button
    const newChatButton = conversationsList.querySelector(`li[data-thread-id="${threadId}"] .conversation-button`);
    newChatButton.addEventListener("click", function() {
        switchToChat(threadId);
    });
}

async function loadChatHistory(threadId) {
    try {
        const response = await fetch(`/chat/${threadId}`);
        const data = await response.json();
        console.log("Chat history data: ", data);
        
        clearConversation();
            
        data.messages.forEach(msg => {
            if (msg.type === 'human') {
                addUserMessage(msg.content);
            } else if (msg.type === 'ai') {
                addAssistantMessageComplete(msg.content);
            }
        });
        
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

async function loadSidebarChats() {
    if (!currentUser) return;

    try {
        console.log("loadSidebarChats called");
        
        const response = await fetch(`/chats/${currentUser.uid}`);
        const data = await response.json();
        console.log("Sidebar chats data: ", data);
        
        const conversationsList = document.querySelector('.conversations');
        const todayGroup = conversationsList.querySelector('li.grouping');
        
        // Clear existing chats (keep grouping)
        const existingChats = conversationsList.querySelectorAll('li:not(.grouping)');
        existingChats.forEach(chat => chat.remove());
        
        // Add each chat to sidebar
        data.chats.forEach(chat => {
            const chatHTML = `
                <li data-thread-id="${chat.thread_id}">
                    <button class="conversation-button"><i class="fa fa-message fa-regular"></i> ${chat.title}</button>
                    <div class="fade"></div>
                    <div class="edit-buttons">
                        <button><i class="fa fa-edit"></i></button>
                        <button><i class="fa fa-trash"></i></button>
                    </div>
                </li>
            `;
            todayGroup.insertAdjacentHTML('afterend', chatHTML);
        });
        
        // Add event listeners to ALL conversation buttons after they're loaded
        setupConversationButtonListeners();
        
    } catch (error) {
        console.error('Failed to load sidebar chats:', error);
    }
}

// Separate function for conversation button listeners
function setupConversationButtonListeners() {
    document.querySelectorAll(".conversation-button").forEach(button => {
        // Remove existing listener to prevent duplicates
        button.removeEventListener("click", handleConversationClick);
        button.addEventListener("click", handleConversationClick);
    });
}

function handleConversationClick() {
    const threadId = this.closest('li').dataset.threadId || "130";
    switchToChat(threadId);
}

// Single event listener setup
function setupEventListeners() {
    // Sidebar toggle
    hide_sidebar.addEventListener("click", function() {
        sidebar.classList.toggle("hidden");
    });

    // User menu (single listener)
    const user_menu = document.querySelector(".user-menu ul");
    const show_user_menu = document.querySelector(".user-menu button");
    
    if (show_user_menu) {
        show_user_menu.addEventListener("click", function() {
            
            // Add logout option to menu if not exists
            if (!user_menu.querySelector('.logout-btn')) {
                const logoutHTML = `<li><button class="logout-btn">Logout</button></li>`;
                user_menu.insertAdjacentHTML('beforeend', logoutHTML);
                
                document.querySelector('.logout-btn').addEventListener('click', logout);
            }

            if (user_menu.classList.contains("show")) {
                user_menu.classList.toggle("show");
                setTimeout(function() {
                    user_menu.classList.toggle("show-animate");
                }, 200);
            } else {
                user_menu.classList.toggle("show-animate");
                setTimeout(function() {
                    user_menu.classList.toggle("show");
                }, 50);
            }
        });
    }

    // Message input auto-resize
    message_box.addEventListener("keyup", function() {
        message_box.style.height = "auto";
        let height = Math.min(message_box.scrollHeight + 2, 200);
        message_box.style.height = height + "px";
    });

    // Send message events
    sendButton.addEventListener('click', function(e) {
        e.preventDefault();
        sendMessage();
    });

    message_box.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // New chat button
    new_chat_button.addEventListener("click", function() {
        clearConversation();
        show_view(".new-chat-view");
        
        // Create new thread_id and WebSocket connection
        const newThreadId = Date.now().toString();
        currentThreadId = newThreadId;
        createWebSocket(newThreadId);
        
        console.log(`New chat started with thread_id: ${newThreadId}`);
    });

}

// Proper initialization order
function init() {
    setupEventListeners();
    createWebSocket(currentThreadId);
    loadSidebarChats(); // This will call setupConversationButtonListeners() after loading
}

// Start everything when page loads
window.addEventListener('DOMContentLoaded', init);

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (ws) {
        ws.close();
    }
});