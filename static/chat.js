// 聊天室前端逻辑
let page = 1;
let loading = false;
let hasMore = true;
const chatHistory = document.getElementById('chat-history');
const sendBtn = document.getElementById('send-btn');
const nicknameInput = document.getElementById('nickname');
const emailInput = document.getElementById('email');
const messageInput = document.getElementById('message');
const emojiBtn = document.getElementById('emoji-btn');
const room = window.CHAT_ROOM;

// localStorage 自动填充
window.addEventListener('DOMContentLoaded', () => {
    const savedNick = localStorage.getItem('chat_nick');
    const savedEmail = localStorage.getItem('chat_email');
    if (savedNick) nicknameInput.value = savedNick;
    if (savedEmail) emailInput.value = savedEmail;
});
nicknameInput.addEventListener('change', () => {
    localStorage.setItem('chat_nick', nicknameInput.value.trim());
});
emailInput.addEventListener('change', () => {
    localStorage.setItem('chat_email', emailInput.value.trim());
});

// 表情插入
const emojis = ["😊", "😂", "👍", "🎉", "🥳", "😎", "❤️", "😄", "😭", "🤔"];
let emojiPanel;
emojiBtn.addEventListener('click', (e) => {
    if (!emojiPanel) {
        emojiPanel = document.createElement('div');
        emojiPanel.className = 'emoji-panel';
        emojis.forEach(emo => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'emoji-item';
            btn.textContent = emo;
            btn.onclick = () => {
                insertAtCursor(messageInput, emo);
                emojiPanel.style.display = 'none';
                messageInput.focus();
            };
            emojiPanel.appendChild(btn);
        });
        emojiBtn.parentNode.appendChild(emojiPanel);
    }
    emojiPanel.style.display = emojiPanel.style.display === 'block' ? 'none' : 'block';
    e.stopPropagation();
});
document.addEventListener('click', () => {
    if (emojiPanel) emojiPanel.style.display = 'none';
});
function insertAtCursor(textarea, text) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;
    textarea.value = value.slice(0, start) + text + value.slice(end);
    textarea.selectionStart = textarea.selectionEnd = start + text.length;
}

// 渲染消息
function renderMessages(messages, prepend = false) {
    const fragment = document.createDocumentFragment();
    messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'chat-message';
        // Markdown 渲染并防 XSS
        const html = DOMPurify.sanitize(marked.parse(msg.content || ""));
        div.innerHTML = `<div class="chat-meta">
            <span class="chat-nick">${msg.nickname}</span>
            <span class="chat-email">&lt;${msg.email}&gt;</span>
            <span class="chat-time">${msg.timestamp}</span>
        </div>
        <div class="chat-content">${html}</div>`;
        fragment.appendChild(div);
    });
    if (prepend) {
        chatHistory.insertBefore(fragment, chatHistory.firstChild);
    } else {
        chatHistory.appendChild(fragment);
    }
}

// 加载历史消息
async function loadHistory(prepend = false) {
    if (loading || !hasMore) return;
    loading = true;
    try {
        const res = await fetch(`/${encodeURIComponent(room)}/history?page=${page}`);
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
            let msgs = data.messages;
            if (prepend) msgs = msgs.reverse();
            renderMessages(msgs, prepend);
            page += 1;
            hasMore = data.has_next;
        } else {
            hasMore = false;
        }
    } catch (e) {
        // ignore
    }
    loading = false;
}

// 发送消息
function validateEmail(email) {
    return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}
async function sendMessage() {
    const nickname = nicknameInput.value.trim();
    const email = emailInput.value.trim();
    const content = messageInput.value.trim();
    if (!nickname || !email || !content) {
        alert('请填写昵称、邮箱和消息');
        return;
    }
    if (!validateEmail(email)) {
        alert('邮箱格式不正确');
        emailInput.focus();
        return;
    }
    localStorage.setItem('chat_nick', nickname);
    localStorage.setItem('chat_email', email);
    sendBtn.disabled = true;
    try {
        const res = await fetch(`/${encodeURIComponent(room)}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname, email, content })
        });
        const data = await res.json();
        if (data.success) {
            renderMessages([data.message]);
            messageInput.value = '';
            chatHistory.scrollTop = chatHistory.scrollHeight;
        } else {
            alert(data.error || '发送失败');
        }
    } catch (e) {
        alert('网络错误');
    }
    sendBtn.disabled = false;
}

// 滚动监听，上拉加载
chatHistory.addEventListener('scroll', () => {
    if (chatHistory.scrollTop === 0 && hasMore && !loading) {
        const oldHeight = chatHistory.scrollHeight;
        loadHistory(true).then(() => {
            // 保持滚动位置
            chatHistory.scrollTop = chatHistory.scrollHeight - oldHeight;
        });
    }
});

// 发送按钮事件
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 初始加载全部历史
window.addEventListener('DOMContentLoaded', async () => {
    // 首次加载第一页历史，reverse 保证顺序旧→新
    const res = await fetch(`/${encodeURIComponent(room)}/history?page=1`);
    const data = await res.json();
    if (data.messages && data.messages.length > 0) {
        renderMessages(data.messages.reverse());
        page = 2;
        hasMore = data.has_next;
        // 渲染后立即滚动到底部
        chatHistory.scrollTop = chatHistory.scrollHeight;
    } else {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});
