/* ═══════════════════════════════════════════════════════════════════════════
   Lee — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════════════════ */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── State ────────────────────────────────────────────────────────────────
let ws = null;
let currentConversationId = null;
let isWaiting = false;
let currentStreamingMessageEl = null;
let currentStreamingContent = "";

// ── DOM References ───────────────────────────────────────────────────────
const sidebar = $("#sidebar");
const sidebarToggle = $("#sidebar-toggle");
const btnNewChat = $("#btn-new-chat");
const searchInput = $("#search-input");
const conversationList = $("#conversation-list");
const welcomeScreen = $("#welcome-screen");
const messagesContainer = $("#messages-container");
const messagesDiv = $("#messages");
const messageInput = $("#message-input");
const btnSend = $("#btn-send");

// ═══════════════════════════════════════════════════════════════════════════
// WEBSOCKET
// ═══════════════════════════════════════════════════════════════════════════
function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => console.log("✅ WebSocket connected");

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
    };

    ws.onclose = () => {
        console.log("⚠️ WebSocket closed, reconnecting in 2s…");
        setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
    };
}

function sendMessage(text) {
    if (!ws || ws.readyState !== WebSocket.OPEN || !text.trim() || isWaiting) return;

    isWaiting = true;
    btnSend.disabled = true;

    // Show the message in the UI immediately
    appendMessage("user", text);

    // Hide welcome, show messages
    showChatView();

    // Show typing indicator
    showTypingIndicator();

    // Send to server
    ws.send(JSON.stringify({
        message: text,
        conversation_id: currentConversationId,
    }));
}

function stopStreaming() {
    currentStreamingMessageEl = null;
    currentStreamingContent = "";
    isWaiting = false;
    updateSendButton();
}

// ═══════════════════════════════════════════════════════════════════════════
// EVENT HANDLING
// ═══════════════════════════════════════════════════════════════════════════
function handleServerEvent(data) {
    switch (data.type) {
        case "conversation_id":
            currentConversationId = data.content;
            loadConversations(); // Refresh sidebar
            break;

        case "tool_call":
            removeTypingIndicator();
            appendToolCall(data.tool_name, data.tool_args, "running");
            break;

        case "tool_result":
            updateToolCallStatus(data.tool_name, "done");
            showTypingIndicator();
            break;

        case "content_chunk":
            removeTypingIndicator();
            appendMessageChunk("assistant", data.content);
            break;

        case "message":
            removeTypingIndicator();
            if (currentStreamingMessageEl) {
                stopStreaming();
            } else {
                appendMessage("assistant", data.content);
                isWaiting = false;
                updateSendButton();
            }
            break;

        case "error":
            removeTypingIndicator();
            if (currentStreamingMessageEl) {
                stopStreaming();
            }
            appendMessage("assistant", `⚠️ ${data.content}`);
            isWaiting = false;
            updateSendButton();
            break;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// MESSAGE RENDERING
// ═══════════════════════════════════════════════════════════════════════════
function appendMessage(role, content) {
    const msgEl = document.createElement("div");
    msgEl.className = `message ${role}`;

    const avatarIcon = role === "user" ? "👤" : "✦";
    const senderName = role === "user" ? "You" : "Lee";

    msgEl.innerHTML = `
        <div class="message-avatar">${avatarIcon}</div>
        <div class="message-body">
            <div class="message-sender">${senderName}</div>
            <div class="message-content">${renderMarkdown(content)}</div>
        </div>
    `;

    messagesDiv.appendChild(msgEl);
    scrollToBottom();
    return msgEl;
}

function appendMessageChunk(role, chunk) {
    if (!currentStreamingMessageEl) {
        currentStreamingMessageEl = appendMessage(role, "");
        currentStreamingContent = "";
    }
    currentStreamingContent += chunk;
    const contentEl = currentStreamingMessageEl.querySelector(".message-content");
    contentEl.innerHTML = renderMarkdown(currentStreamingContent);
    scrollToBottom();
}

function appendToolCall(toolName, toolArgs, status) {
    const el = document.createElement("div");
    el.className = `tool-call ${status}`;
    el.id = `tool-${toolName}-${Date.now()}`;
    el.dataset.toolName = toolName;

    const argsStr = Object.entries(toolArgs || {})
        .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
        .join(", ");

    el.innerHTML = `
        <span class="tool-icon">🔧</span>
        <span>Using <span class="tool-name">${toolName}</span>${argsStr ? ` — ${escapeHtml(argsStr)}` : ""}</span>
    `;

    messagesDiv.appendChild(el);
    scrollToBottom();
}

function updateToolCallStatus(toolName, status) {
    const tools = messagesDiv.querySelectorAll(`.tool-call[data-tool-name="${toolName}"]`);
    const el = tools[tools.length - 1]; // Get the latest one
    if (el) {
        el.className = `tool-call ${status}`;
    }
}

function showTypingIndicator() {
    if ($("#typing-indicator")) return;
    const el = document.createElement("div");
    el.className = "typing-indicator";
    el.id = "typing-indicator";
    el.innerHTML = `
        <div class="message-avatar" style="background: linear-gradient(135deg, var(--accent-start), var(--accent-mid)); box-shadow: 0 0 12px var(--accent-glow);">✦</div>
        <div class="typing-dots">
            <span></span><span></span><span></span>
        </div>
    `;
    messagesDiv.appendChild(el);
    scrollToBottom();
}

function removeTypingIndicator() {
    const el = $("#typing-indicator");
    if (el) el.remove();
}

// ═══════════════════════════════════════════════════════════════════════════
// MARKDOWN RENDERING (lightweight)
// ═══════════════════════════════════════════════════════════════════════════
function renderMarkdown(text) {
    if (!text) return "";

    let html = escapeHtml(text);

    // Code blocks (```...```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Headers
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Blockquotes
    html = html.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");

    // Unordered lists
    html = html.replace(/^[\-\*] (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Horizontal rules
    html = html.replace(/^---$/gm, "<hr>");

    // Line breaks → paragraphs
    html = html.replace(/\n\n/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");

    // Wrap in paragraph if doesn't start with block element
    if (!/^<[hpuolbtd]/.test(html)) {
        html = `<p>${html}</p>`;
    }

    return html;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════════════════════
// CONVERSATIONS SIDEBAR
// ═══════════════════════════════════════════════════════════════════════════
async function loadConversations() {
    try {
        const res = await fetch("/api/conversations");
        const convs = await res.json();
        renderConversationList(convs);
    } catch (e) {
        console.error("Failed to load conversations:", e);
    }
}

function renderConversationList(conversations) {
    conversationList.innerHTML = "";

    if (conversations.length === 0) {
        conversationList.innerHTML = `
            <div style="text-align: center; padding: 30px 16px; color: var(--text-muted); font-size: 0.8rem;">
                No conversations yet.<br>Start chatting!
            </div>
        `;
        return;
    }

    conversations.forEach((conv) => {
        const el = document.createElement("div");
        el.className = `conv-item${conv.id === currentConversationId ? " active" : ""}`;
        el.dataset.id = conv.id;

        const channelIcon = conv.channel === "discord" ? "💬" : "💭";

        el.innerHTML = `
            <span class="conv-icon">${channelIcon}</span>
            <span class="conv-title" title="${escapeHtml(conv.title)}">${escapeHtml(conv.title)}</span>
            <button class="conv-delete" title="Delete" onclick="event.stopPropagation(); deleteConversation('${conv.id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        `;

        el.addEventListener("click", () => loadConversation(conv.id));
        conversationList.appendChild(el);
    });
}

async function loadConversation(convId) {
    try {
        const res = await fetch(`/api/conversations/${convId}`);
        if (!res.ok) return;
        const data = await res.json();

        currentConversationId = convId;
        messagesDiv.innerHTML = "";
        showChatView();

        // Render messages, skip tool messages and tool-call markers
        data.messages.forEach((msg) => {
            if (msg.role === "tool") return;
            if (msg.role === "assistant" && msg.content.startsWith("[Tool Call:")) {
                // Show as a completed tool call indicator
                const match = msg.content.match(/\[Tool Call: (\w+)\(/);
                if (match) {
                    appendToolCall(match[1], {}, "done");
                }
                return;
            }
            appendMessage(msg.role, msg.content);
        });

        // Update sidebar active state
        $$(".conv-item").forEach((el) => {
            el.classList.toggle("active", el.dataset.id === convId);
        });

        // Close sidebar on mobile
        sidebar.classList.remove("open");
    } catch (e) {
        console.error("Failed to load conversation:", e);
    }
}

async function deleteConversation(convId) {
    try {
        await fetch(`/api/conversations/${convId}`, { method: "DELETE" });
        if (convId === currentConversationId) {
            startNewChat();
        }
        loadConversations();
    } catch (e) {
        console.error("Failed to delete conversation:", e);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════════════════════════════════════
function showChatView() {
    welcomeScreen.style.display = "none";
    messagesContainer.style.display = "flex";
}

function showWelcomeView() {
    welcomeScreen.style.display = "flex";
    messagesContainer.style.display = "none";
}

function startNewChat() {
    currentConversationId = null;
    messagesDiv.innerHTML = "";
    showWelcomeView();
    messageInput.focus();
    $$(".conv-item").forEach((el) => el.classList.remove("active"));
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });
}

function updateSendButton() {
    btnSend.disabled = !messageInput.value.trim() || isWaiting;
}

function autoResizeTextarea() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + "px";
}

// ═══════════════════════════════════════════════════════════════════════════
// EVENT LISTENERS
// ═══════════════════════════════════════════════════════════════════════════

// Send message
btnSend.addEventListener("click", () => {
    const text = messageInput.value.trim();
    if (text) {
        sendMessage(text);
        messageInput.value = "";
        autoResizeTextarea();
    }
});

// Enter to send, Shift+Enter for new line
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        btnSend.click();
    }
});

// Auto-resize textarea
messageInput.addEventListener("input", () => {
    updateSendButton();
    autoResizeTextarea();
});

// New chat
btnNewChat.addEventListener("click", startNewChat);

// Sidebar toggle (mobile)
sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
});

// Close sidebar when clicking outside on mobile
document.addEventListener("click", (e) => {
    if (window.innerWidth <= 768 && sidebar.classList.contains("open")) {
        if (!sidebar.contains(e.target) && e.target !== sidebarToggle) {
            sidebar.classList.remove("open");
        }
    }
});

// Quick actions
$$(".quick-action").forEach((btn) => {
    btn.addEventListener("click", () => {
        const msg = btn.dataset.message;
        messageInput.value = msg;
        updateSendButton();
        btnSend.click();
    });
});

// Search conversations
searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    $$(".conv-item").forEach((el) => {
        const title = el.querySelector(".conv-title").textContent.toLowerCase();
        el.style.display = title.includes(query) ? "" : "none";
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════
connectWebSocket();
loadConversations();
messageInput.focus();
