// 聊天室前端逻辑
let page = 1; // This might become less relevant with before_id, but keep for initial load fallback
let loading = false;
let hasMoreOlderMessages = true; // Indicates if there are more *older* messages to load
let lastMessageId = 0; // 记录当前已加载的最新消息ID (用于获取新消息)
const chatHistory = document.getElementById("chat-history");
const sendBtn = document.getElementById("send-btn");
const nicknameInput = document.getElementById("nickname");
const emailInput = document.getElementById("email");
const messageInput = document.getElementById("message");
const emojiBtn = document.getElementById("emoji-btn");
const room = window.CHAT_ROOM;

// localStorage 自动填充
window.addEventListener("DOMContentLoaded", () => {
  const savedNick = localStorage.getItem("chat_nick");
  const savedEmail = localStorage.getItem("chat_email");
  if (savedNick) nicknameInput.value = savedNick;
  if (savedEmail) emailInput.value = savedEmail;
});
nicknameInput.addEventListener("change", () => {
  localStorage.setItem("chat_nick", nicknameInput.value.trim());
});
emailInput.addEventListener("change", () => {
  localStorage.setItem("chat_email", emailInput.value.trim());
});

// 表情插入
const emojis = ["😊", "😂", "👍", "🎉", "🥳", "😎", "❤️", "😄", "😭", "🤔"];
let emojiPanel;
emojiBtn.addEventListener("click", (e) => {
  if (!emojiPanel) {
    emojiPanel = document.createElement("div");
    emojiPanel.className = "emoji-panel";
    emojis.forEach((emo) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "emoji-item";
      btn.textContent = emo;
      btn.onclick = () => {
        insertAtCursor(messageInput, emo);
        emojiPanel.style.display = "none";
        messageInput.focus();
      };
      emojiPanel.appendChild(btn);
    });
    emojiBtn.parentNode.appendChild(emojiPanel);
  }
  emojiPanel.style.display =
    emojiPanel.style.display === "block" ? "none" : "block";
  e.stopPropagation();
});
document.addEventListener("click", () => {
  if (emojiPanel) emojiPanel.style.display = "none";
});
function insertAtCursor(textarea, text) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = textarea.value;
  textarea.value = value.slice(0, start) + text + value.slice(end);
  textarea.selectionStart = textarea.selectionEnd = start + text.length;
}

// 渲染消息
function renderMessages(messages, prepend = false) { // Removed autoScroll parameter
  const fragment = document.createDocumentFragment();
  messages.forEach((msg) => {
    const div = document.createElement("div");
    div.className = "chat-message";
    div.dataset.messageId = msg.id; // 添加数据属性存储消息ID
    // Markdown 渲染并防 XSS
    const html = DOMPurify.sanitize(marked.parse(msg.content || ""));
    div.innerHTML = `<div class="chat-meta">
            <span class="chat-nick">${msg.nickname}</span>
            <span class="chat-email"><${msg.email}></span>
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
  // Removed scrolling logic
}

async function loadMessages({
  type = "initial",
  sinceId = 0,
  beforeId = 0,
} = {}) {
  // Only prevent loading for 'initial' and 'older' types if already loading
  if (loading && (type === "initial" || type === "older")) return;

  // Capture scroll state BEFORE fetching/rendering
  const oldScrollHeight = chatHistory.scrollHeight;
  const isUserAtBottomBeforeFetch = chatHistory.scrollHeight - chatHistory.scrollTop <= chatHistory.clientHeight + 50; // 50px threshold

  // Set loading to true only for 'initial' and 'older' types
  if (type === "initial" || type === "older") {
      loading = true;
  }

  let url = `/${encodeURIComponent(room)}/history`;
  if (type === "new") {
    url += `?since_id=${sinceId}`;
    console.log(`Fetching new messages since ID: ${sinceId}`); // Debug log
  } else if (type === "older") {
    url += `?before_id=${beforeId}`;
    console.log(`Fetching older messages before ID: ${beforeId}`); // Debug log
  } else { // type === 'initial'
    url += `?page=1`; // Initial load still uses page 1 for the newest batch
    console.log(`Fetching initial messages (page 1)`); // Debug log
  }

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.messages && data.messages.length > 0) {
      console.log(`Fetched messages (${type}):`, data.messages.map(msg => msg.id)); // Debug log
      if (type === "older") {
        // For older messages, they are fetched in desc order, reverse to prepend in asc order
        renderMessages(data.messages.reverse(), true); // Prepend
        hasMoreOlderMessages = data.has_next; // Update hasMoreOlderMessages for older messages

        // Restore scroll position after prepending
        requestAnimationFrame(() => {
          chatHistory.scrollTop = chatHistory.scrollHeight - oldScrollHeight;
        });

      } else { // 'initial' or 'new'
        let msgsToRender = data.messages;
        if (type === "initial") {
          // For initial load, messages are fetched newest first (desc),
          // but we want to render them oldest first to appear at the bottom correctly.
          msgsToRender = msgsToRender.reverse();
          console.log("Initial messages (rendered order):", msgsToRender.map(msg => msg.id)); // Debug log
        }

        renderMessages(msgsToRender, false); // Append

        // Update lastMessageId only for 'initial' and 'new' fetches
        // lastMessageId should be the ID of the absolute newest message fetched
        if (data.messages.length > 0) {
          lastMessageId = data.messages[data.messages.length - 1].id; // Use original data.messages for newest ID
          console.log("Updated lastMessageId:", lastMessageId); // Debug log
        }

        // Scroll logic AFTER rendering
        if (type === "initial") {
          // Always scroll to bottom on initial load
          requestAnimationFrame(() => {
            chatHistory.scrollTop = chatHistory.scrollHeight;
          });
        } else if (type === "new" && isUserAtBottomBeforeFetch) {
          // Scroll to bottom for new messages ONLY if user was at bottom before fetch
           requestAnimationFrame(() => {
            chatHistory.scrollTop = chatHistory.scrollHeight;
          });
        }
      }
    } else {
      console.log(`No messages fetched for type: ${type}`); // Debug log
      if (type === "older") {
        hasMoreOlderMessages = false; // No more older messages
      }
    }
  } catch (e) {
    console.error(`加载消息失败 (${type}):`, e);
  } finally {
    // Always set loading to false for 'initial' and 'older' types
    if (type === "initial" || type === "older") {
        loading = false;
    }
  }
}

// 获取新消息 (轮询) - Now uses loadMessages
async function fetchNewMessages() {
  loadMessages({ type: "new", sinceId: lastMessageId });
}

// 滚动监听，上拉加载 - Now uses loadMessages with before_id
chatHistory.addEventListener("scroll", () => {
  // 恢复到精确顶部触发，并尝试修复滚动位置恢复问题
  //console.log(chatHistory.scrollTop, hasMoreOlderMessages, loading); // Debug log
  if (chatHistory.scrollTop === 0 && hasMoreOlderMessages && !loading) {
    const oldHeight = chatHistory.scrollHeight;
    // Get the ID of the oldest message currently displayed
    const oldestMessageElement = chatHistory.querySelector(".chat-message");
    if (oldestMessageElement) {
      const oldestMessageId = parseInt(
        oldestMessageElement.dataset.messageId,
        10
      );
      if (!isNaN(oldestMessageId)) {
        loadMessages({ type: "older", beforeId: oldestMessageId }).then(() => {
          // Keep scroll position - try setTimeout 0ms
          setTimeout(() => {
            chatHistory.scrollTop = chatHistory.scrollHeight - oldHeight;
          }, 0);
        });
      }
    } else {
      // If no messages are displayed, maybe load the first page of history?
      // This case should ideally not happen if initial load works.
      console.warn(
        "No message elements found to determine oldest ID for history load."
      );
      // Fallback to loading page 1 if no messages are present? Or just stop?
      // Let's assume initial load always puts some messages.
    }
  }
});

// 发送消息
function validateEmail(email) {
  return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
}
async function sendMessage() {
  const nickname = nicknameInput.value.trim();
  const email = emailInput.value.trim();
  const content = messageInput.value.trim();
  if (!nickname || !email || !content) {
    alert("请填写昵称、邮箱和消息");
    return;
  }
  if (!validateEmail(email)) {
    alert("邮箱格式不正确");
    emailInput.focus();
    return;
  }
  localStorage.setItem("chat_nick", nickname);
  localStorage.setItem("chat_email", email);
  sendBtn.disabled = true;
  try {
    const res = await fetch(`/${encodeURIComponent(room)}/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nickname, email, content }),
    });
    const data = await res.json();
    if (data.success) {
      // renderMessages([data.message], false, true); // 不再立即渲染发送的消息
      messageInput.value = "";
    } else {
      alert(data.error || "发送失败");
    }
  } catch (e) {
    alert("网络错误");
  }
  sendBtn.disabled = false;
}


// 发送按钮事件
sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// 生成唯一client_id（每个页面唯一，刷新/新开页不同）
function getClientId() {
  let cid = sessionStorage.getItem("chat_client_id");
  if (!cid) {
    // Use timestamp + random number to ensure uniqueness
    cid = Date.now() + "-" + Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem("chat_client_id", cid);
  }
  return cid;
}

// 初始加载和定时刷新
window.addEventListener("DOMContentLoaded", async () => {
  // 首次加载最新一批历史消息 (page 1)
  await loadMessages({ type: "initial" }); // 使用新的loadMessages函数


  // 心跳包定时器
  const client_id = getClientId();
  fetch(`/${encodeURIComponent(room)}/heartbeat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id }),
  });
  setInterval(() => {
    fetch(`/${encodeURIComponent(room)}/heartbeat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id }),
    });
  }, 10000);

  // 新消息轮询定时器 (每1秒检查一次新消息)
  setInterval(fetchNewMessages, 1000);
});
