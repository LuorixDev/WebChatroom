# WebChatroom

一个功能完善、安全可靠的网页聊天室应用，基于 Flask 和 SQLite 构建。它支持多房间聊天、新设备邮件验证、实时在线人数统计和消息历史记录等功能。

## 主要功能

*   **多聊天室**：支持创建多个独立的聊天室，每个聊天室拥有自己的数据库，确保数据隔离。
*   **新设备邮件验证**：用户在新的设备上首次发言时，需要通过邮件链接进行验证，增强了账户的安全性。
*   **实时在线人数**：通过心跳机制，实时显示当前聊天室的在线用户数量。
*   **丰富的消息体验**：
    *   支持 Markdown 语法，可以发送代码块、列表等格式。
    *   内置表情符号选择器。
    *   输入内容经过 DOMPurify 安全过滤，有效防止 XSS 攻击。
*   **完善的消息历史记录**：
    *   **首次加载**：进入聊天室时，自动加载最新的消息。
    *   **增量加载**：每秒自动获取新消息，并平滑滚动到底部。
    *   **滚动加载**：向上滚动到顶部时，自动加载更早的历史消息。
*   **管理员权限**：管理员可以删除聊天室中的任何消息。
*   **本地信息缓存**：用户的昵称和邮箱地址会缓存在本地，方便下次使用。

## 技术栈

*   **后端**：Flask, SQLAlchemy
*   **数据库**：SQLite
*   **邮件服务**：Flask-Mail
*   **前端**：原生 JavaScript, Marked.js, DOMPurify
*   **部署**：可通过 Gunicorn + Nginx 等方式部署

## 部署与运行

1.  **克隆项目**
    ```bash
    git clone https://github.com/LuorixDev/WebChatroom.git
    cd WebChatroom
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置**
    *   复制 `config.py.example` 为 `config.py`。
    *   修改 `config.py` 文件中的配置项，特别是 `SECRET_KEY` 和邮件服务器相关的设置（`MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` 等）。
    *   设置管理员邮箱 `ADMIN_EMAIL`。

4.  **运行**
    ```bash
    python run.py
    ```
    应用默认运行在 `http://0.0.0.0:18765`。

5.  **访问**
    在浏览器中打开 `http://<your-server-ip>:18765/<room-name>/room` 即可进入指定名称的聊天室。例如：`http://127.0.0.1:18765/general/room`。

## API 接口

| 方法   | 路径                               | 功能                 |
| ------ | ---------------------------------- | -------------------- |
| POST   | `/<room-name>/send`                | 发送消息             |
| GET    | `/<room-name>/history`             | 获取消息历史         |
| POST   | `/<room-name>/heartbeat`           | 发送心跳             |
| GET    | `/<room-name>/onlinecount`         | 获取在线人数         |
| POST   | `/<room-name>/delete/<message_id>` | 删除消息（管理员）   |
| GET    | `/confirm/<token>`                 | 验证设备             |

## 未来计划

*   [ ] 支持文件上传和图片发送
*   [ ] 引入 WebSocket 以实现更实时的通信
*   [ ] 优化前端界面和用户体验
