# WebChatroom

![Python](https://img.shields.io/badge/python-3.x-blue.svg) ![Flask](https://img.shields.io/badge/flask-framework-blue.svg) ![License](https://img.shields.io/badge/license-MIT%20or%20Apache%202.0-blue.svg)

一个基于 Flask 和 SQLite 的简单网页聊天室应用。

## 项目简介

这是一个轻量级的网页聊天室应用，后端使用 Python Flask 框架，前端使用 HTML、CSS 和原生 JavaScript。数据存储采用 SQLite 数据库，每个聊天室对应一个独立的数据库文件。项目实现了基本的聊天功能，包括发送消息、加载历史消息（支持分页和上拉加载）、以及一个简易的在线人数统计（通过心跳包实现）。

[![](example/example.png)]([超链接地址](https://webchatroom.dimeta.top/githubreadme/room]))

---

## 在线 Demo

你可以访问以下地址体验在线 Demo：

[https://webchatroom.dimeta.top/githubreadme/room](https://webchatroom.dimeta.top/githubreadme/room)

---

## 主要特性

*   **后端**:
    *   基于 Flask 框架。
    *   使用 SQLAlchemy ORM 操作 SQLite 数据库。
    *   每个聊天室使用独立的 `.db` 文件存储数据，文件位于 `instance/` 目录下。
    *   实现消息发送 (`/<name>/send`)、历史消息获取 (`/<name>/history`) 和心跳包 (`/<name>/heartbeat`) 等 API 接口。
    *   历史消息接口支持多种模式：首次加载最新消息、获取指定 ID 之后的新消息、获取指定 ID 之前的历史消息（用于上拉加载）。
    *   通过心跳包和定时清理机制实现简易的在线人数统计 (`/<name>/onlinecount`)。
    *   使用 Flask-CORS 处理跨域请求。

*   **前端**:
    *   使用 HTML 构建页面结构。
    *   使用 CSS 进行样式美化，实现响应式布局（针对移动端优化）。
    *   使用原生 JavaScript 实现前端逻辑。
    *   通过 AJAX 与后端 API 进行交互。
    *   实现消息的实时加载（通过轮询获取新消息）。
    *   实现聊天记录的上拉加载更多历史消息。
    *   支持昵称和邮箱的本地存储，方便用户下次访问。
    *   集成 `marked.js` 支持 Markdown 格式的消息内容。
    *   集成 `DOMPurify` 防止 XSS 攻击。
    *   提供简单的表情插入功能。
    *   通过心跳包机制告知后端用户在线状态。

---

## 项目结构

```
.
├── instance/             # 存放各个聊天室的 SQLite 数据库文件
├── static/
│   ├── chat.css          # 聊天室页面样式
│   └── chat.js           # 聊天室前端逻辑
├── templates/
│   └── room.html         # 聊天室页面 HTML 模板
└── run.py                # Flask 应用主文件，包含后端路由和逻辑
```

---

## 部署与运行

1.  **克隆仓库**:
    ```bash
    git clone <仓库地址>
    cd WebChatroom
    ```
2.  **安装依赖**:
    确保你的系统安装了 Python 3。然后安装所需的 Python 库：
    ```bash
    pip install Flask Flask-Cors SQLAlchemy
    ```
3.  **运行应用**:
    ```bash
    python run.py
    ```
    应用将默认运行在 `http://0.0.0.0:18765/`。

4.  **访问聊天室**:
    打开浏览器，访问 `http://localhost:18765/<房间名>/room`，将 `<房间名>` 替换为你想要进入的聊天室名称（例如：`http://localhost:18765/general/room`）。如果该房间不存在，访问时会自动创建对应的数据库文件。

---

## 技术栈

*   **后端**: Python 3, Flask, SQLAlchemy, SQLite
*   **前端**: HTML, CSS, JavaScript, marked.js, DOMPurify

---

## 待办事项/可改进之处

*   使用 WebSocket 实现消息的实时推送，替代当前的轮询机制，提高效率和实时性。
*   增加用户认证和管理功能。
*   完善错误处理和日志记录。
*   优化前端性能，特别是大量消息时的渲染效率。
*   增加更多的配置选项（如端口号、数据库路径等）。
*   考虑使用更健壮的数据库系统（如 PostgreSQL, MySQL）以支持更大规模的应用。

---

## 贡献

欢迎提交 Pull Request 或 Issue。

---

## 许可证

MIT

---

## 作为组件嵌入其他网页

本项目可以将聊天室作为一个可拖动的组件嵌入到任何其他网页中。这对于在你的博客、网站或其他应用中提供一个简单的聊天功能非常有用。

Example：[洛元の小屋](https://blog.dimeta.top/)

### 嵌入方法

将以下 HTML、CSS 和 JavaScript 代码添加到你的网页的 `<body>` 标签内。你可以根据需要调整样式。

```html
<!-- 聊天室组件的 HTML 结构 -->
<div id="chat-guide" style="display: none;">✨ 无需登录，欢迎留下你的话语~</div>

<div id="chat-toggle" aria-label="打开聊天室按钮" role="button" tabindex="0">
  <span style="font-size: 12px; color: gray; margin-top: 8px;">可拖动</span>
  <span>说</span>
  <span>点</span>
  <span>什</span>
  <span>么</span>
  <div id="online-count" style="font-size: 12px; color: gray; margin-top: 8px;">
    当前<span id="online-count-number" style="color: green;">加载中...</span>人在线
  </div>
</div>

<div id="chat-box" aria-live="polite" aria-label="聊天室窗口">
  <div id="chat-header">
    💬 网页聊天室（可拖动）
    <div>
      <button id="minimize-btn" aria-label="最小化聊天室窗口">_</button>
      <button id="close-btn" aria-label="关闭聊天室窗口">×</button>
    </div>
  </div>
  <iframe id="chat-content" src="YOUR_CHATROOM_URL/<房间名>/room"></iframe> <!-- 将 YOUR_CHATROOM_URL 替换为你实际部署的地址 -->
</div>

<!-- 聊天室组件的 CSS 样式 -->
<style>
  :root {
    --tianyi-blue: #3087ff;
    --tianyi-light: #e6f0ff;
    --tianyi-blue-p3: color(display-p3 0.19 0.53 1);
    --tianyi-light-p3: color(display-p3 0.9 0.95 1);
  }

  #chat-guide {
    position: fixed;
    top: 45%;
    right: 70px;
    transform: translateY(-50%);
    background: var(--tianyi-light);
    color: var(--tianyi-blue);
    padding: 8px 14px;
    font-size: 12px;
    border-radius: 10px;
    z-index: 9999;
    animation: sparkle-default 1.2s ease-in-out infinite;
    box-shadow: 0 0 10px rgba(48, 135, 255, 0.2);
    font-family: "Smiley Sans", "PingFang SC", "Microsoft YaHei", sans-serif;
    pointer-events: none;
  }

  @keyframes sparkle-default {
    0%, 30%, 70%, 100% { opacity: 1; transform: scale(1); }
    40%, 60% { opacity: 0.4; transform: scale(1.05); }
    50% { opacity: 0.7; transform: scale(1.02); }
  }

  @media (color-gamut: p3), (color-gamut: rec2020) {
    #chat-guide {
      background: var(--tianyi-light-p3);
      color: var(--tianyi-blue-p3);
      box-shadow: 0 0 20px color(display-p3 0.19 0.53 1 / 0.6);
      animation: sparkle-hdr 1.5s ease-in-out infinite;
    }

    @keyframes sparkle-hdr {
      0%, 25% {
        opacity: 1;
        transform: scale(1);
        filter: drop-shadow(0 0 8px color(display-p3 0.19 0.53 1));
      }
      50% {
        opacity: 0.4;
        transform: scale(1.05);
        filter: drop-shadow(0 0 20px color(display-p3 0.19 0.53 1));
      }
      75%, 100% {
        opacity: 1;
        transform: scale(1);
        filter: drop_shadow(0 0 10px color(display-p3 0.19 0.53 1));
      }
    }
  }

  #chat-toggle {
    position: fixed;
    top: 45%;
    right: 0;
    transform: translateY(-50%);
    background: #00daff;
    color: white;
    padding: 10px 4px;
    cursor: pointer;
    font-size: 14px;
    z-index: 10000;
    border-radius: 10px 0 0 10px;
    box-shadow: 0 0 10px rgba(48, 135, 255, 0.4);
    font-family: "Smiley Sans", "PingFang SC", sans-serif;
    text-align: center;
    line-height: 1.4;
    display: flex;
    flex-direction: column;
    align-items: center;
    user-select: none;
  }

  #chat-toggle span {
    display: block;
  }

  #chat-toggle span:last-child {
    margin-top: 6px;
    font-size: 12px;
    opacity: 0.7;
  }

  #chat-box {
    position: fixed;
    width: 80vw;
    height: 60vh;
    bottom: 10vh;
    right: 10vw;
    backdrop-filter: blur(10px);
    background: #ffffffee;
    border: 2px solid var(--tianyi-blue);
    border-radius: 14px;
    box-shadow: 0 0 20px rgba(48, 135, 255, 0.3);
    z-index: 9998;
    display: none;
    flex-direction: column;
    animation: fadeInUp 0.4s ease;
    user-select: none;
    resize: both;
    overflow: auto;
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  #chat-header {
    background: var(--tianyi-blue);
    color: white;
    padding: 6px 14px;
    font-size: 14px;
    font-weight: bold;
    font-family: "Smiley Sans", "PingFang SC", sans-serif;
    cursor: move;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
  }

  #chat-header button {
    background: none;
    border: none;
    color: white;
    font-size: 14px;
    cursor: pointer;
    margin-left: 6px;
  }

  #chat-content {
    flex: 1;
    width: 100%;
    height: 100%;
    border: none;
    border-top: 1px solid var(--tianyi-light);
  }
</style>

<!-- 聊天室组件的 JavaScript 逻辑 -->
<script>
  const toggleBtn = document.getElementById('chat-toggle');
  const chatBox = document.getElementById('chat-box');
  const guide = document.getElementById('chat-guide');
  const closeBtn = document.getElementById('close-btn');
  const minimizeBtn = document.getElementById('minimize-btn');
  const chatHeader = document.getElementById('chat-header');

  const guideShownKey = 'chatWidgetClicked';
  if (!localStorage.getItem(guideShownKey)) {
    guide.style.display = 'block';
  }

  let chatBoxVisible = false;

  toggleBtn.addEventListener('click', () => {
    chatBoxVisible = !chatBoxVisible;
    chatBox.style.display = chatBoxVisible ? 'flex' : 'none';
    guide.style.display = 'none';
    localStorage.setItem(guideShownKey, '1');
  });

  minimizeBtn.addEventListener('click', () => {
    chatBox.style.display = 'none';
    chatBoxVisible = false;
  });

  closeBtn.addEventListener('click', () => {
    chatBox.style.display = 'none';
    chatBoxVisible = false;
  });

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function makeDraggable(element, handle = element) {
    let isDragging = false, offsetX = 0, offsetY = 0;

    const startDrag = (clientX, clientY) => {
      const rect = element.getBoundingClientRect();
      offsetX = clientX - rect.left;
      offsetY = clientY - rect.top;
      isDragging = true;
      document.body.style.userSelect = 'none';
    };

    const onMove = (clientX, clientY) => {
      if (!isDragging) return;
      let left = clientX - offsetX;
      let top = clientY - offsetY;

      const maxLeft = window.innerWidth - element.offsetWidth;
      const maxTop = window.innerHeight - element.offsetHeight;
      left = clamp(left, 0, maxLeft);
      top = clamp(top, 0, maxTop);

      element.style.left = left + 'px';
      element.style.top = top + 'px';
      element.style.right = 'auto';
      element.style.bottom = 'auto';
    };

    handle.addEventListener('mousedown', e => {
      e.preventDefault();
      startDrag(e.clientX, e.clientY);
    });

    handle.addEventListener('touchstart', e => {
      if (e.touches.length > 0) {
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: false });

    document.addEventListener('mousemove', e => onMove(e.clientX, e.clientY));
    document.addEventListener('touchmove', e => {
      if (e.touches.length > 0) onMove(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: false });

    document.addEventListener('mouseup', () => {
      isDragging = false;
      document.body.style.userSelect = '';
    });
    document.addEventListener('touchend', () => {
      isDragging = false;
      document.body.style.userSelect = '';
    });
  }

  makeDraggable(toggleBtn);
  makeDraggable(chatBox, chatHeader);

  toggleBtn.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleBtn.click();
    }
  });

  // 在线人数获取
  document.addEventListener("DOMContentLoaded", function () {
    const onlineCountElement = document.getElementById('online-count-number');
    function fetchOnlineCount() {
      fetch('YOUR_CHATROOM_URL/<房间名>/onlinecount') <!-- 将 YOUR_CHATROOM_URL 替换为你实际部署的地址 -->
        .then(response => response.json())
        .then(data => {
          onlineCountElement.textContent =
            data && typeof data.online === 'number' ? data.online : '未知';
        })
        .catch(() => {
          onlineCountElement.textContent = '错误';
        });
    }
    fetchOnlineCount();
    setInterval(fetchOnlineCount, 10000);
  });
</script>
```

### 原理介绍

该嵌入组件通过以下方式工作：

1.  **HTML 结构**: 定义了一个切换按钮 (`#chat-toggle`) 和一个聊天窗口容器 (`#chat-box`)。聊天窗口容器内包含一个 `<iframe>` 元素 (`#chat-content`)。
2.  **CSS 样式**: 提供组件的布局、外观和动画效果。使用固定定位 (`position: fixed`) 使组件悬浮在页面上。
3.  **JavaScript 逻辑**:
    *   控制切换按钮和聊天窗口的显示/隐藏。
    *   实现聊天窗口和切换按钮的拖动功能。
    *   通过修改 `<iframe>` 的 `src` 属性加载实际的聊天室页面。你需要将 `src` 指向你部署的聊天室应用的 `/<房间名>/room` 路由。
    *   定时向你部署的聊天室应用的 `/<房间名>/onlinecount` 接口发送请求，获取并显示当前在线人数。
    *   使用 `localStorage` 记录用户是否已点击过切换按钮，以控制提示信息的显示。
    *   使用 `sessionStorage` 为每个浏览器会话生成唯一的 `client_id` 用于心跳包（尽管心跳包逻辑在 iframe 加载的页面中，但这里的 `client_id` 生成逻辑是用户提供的嵌入代码的一部分）。

通过这种方式，你无需修改现有网页的复杂结构，只需插入这段代码即可拥有一个功能性的聊天室组件。请确保将代码中的 `YOUR_CHATROOM_URL` 和 `<房间名>` 占位符替换为你实际部署的地址和想要使用的房间名称。
