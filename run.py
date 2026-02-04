from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import g
from flask_mail import Mail, Message as MailMessage
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import markdown
import config
import re

app = Flask(__name__)
app.config.from_pyfile('config.py')

CORS(app)
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# 定义数据库模型
Base = declarative_base()
UserBase = declarative_base()

class VerifiedDevice(UserBase):
    __tablename__ = 'verified_devices'
    id = Column(Integer, primary_key=True)
    email = Column(String(128), index=True)
    device_id = Column(String(128), unique=True)

class PendingRoom(UserBase):
    __tablename__ = 'pending_rooms'
    id = Column(Integer, primary_key=True)
    room_name = Column(String(64), unique=True, index=True)
    status = Column(String(20), default='pending') # pending, approved, denied
    timestamp = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    room = Column(String(64), index=True) # 虽然每个db一个房间，但保留room字段以备将来扩展或查询
    nickname = Column(String(64))
    email = Column(String(128))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'room': self.room,
            'nickname': self.nickname,
            'email': self.email,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class Heartbeat(Base):
    __tablename__ = 'heartbeats'
    id = Column(Integer, primary_key=True)
    room = Column(String(64), index=True) # 同上，保留room字段
    client_id = Column(String(64), index=True)
    last_beat = Column(DateTime, default=datetime.utcnow)

def get_user_db_session():
    if 'user_db_session' not in g:
        db_dir = 'instance'
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join(db_dir, 'users.db')
        db_uri = f'sqlite:///{db_path}'
        engine = create_engine(db_uri)
        UserBase.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        g.user_db_session = Session()
    return g.user_db_session

# 动态获取数据库会话
def get_db_session(room_name, create_if_not_exist=True):
    # 检查g对象是否已经存在session
    if 'db_session' not in g:
        db_dir = 'instance'
        db_path = os.path.join(db_dir, f'{room_name}.db')
        
        if not os.path.exists(db_path) and not create_if_not_exist:
            return None

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        db_uri = f'sqlite:///{db_path}'
        engine = create_engine(db_uri)
        Base.metadata.create_all(engine) # 确保表存在
        Session = sessionmaker(bind=engine)
        g.db_session = Session() # 将session存储在g对象中
    return g.db_session

def is_room_approved(room_name):
    """Check if a room's database file exists."""
    db_path = os.path.join('instance', f'{room_name}.db')
    return os.path.exists(db_path)

# 在请求结束后关闭数据库会话
@app.teardown_request
def remove_session(exception=None):
    # 从g对象获取session，如果存在则关闭
    session = g.pop('db_session', None)
    if session is not None:
        session.close()
    user_session = g.pop('user_db_session', None)
    if user_session is not None:
        user_session.close()


# 心跳包接口
@app.route('/<name>/heartbeat', methods=['POST'])
def heartbeat(name):
    if not is_room_approved(name):
        return jsonify({'success': False, 'error': 'Room not found or not approved'}), 404
    session = get_db_session(name)

    data = request.json
    client_id = data.get('client_id', '').strip()
    if not client_id:
        # session将在teardown_request中关闭，这里不需要提前关闭
        return jsonify({'success': False, 'error': '缺少client_id'}), 400

    # 删除超时的心跳包记录
    timeout_threshold = datetime.utcnow() - timedelta(seconds=30)
    session.query(Heartbeat).filter_by(room=name).filter(Heartbeat.last_beat < timeout_threshold).delete()
    session.commit()

    hb = session.query(Heartbeat).filter_by(room=name, client_id=client_id).first()
    now = datetime.utcnow()
    if hb:
        hb.last_beat = now
    else:
        hb = Heartbeat(room=name, client_id=client_id, last_beat=now)
        session.add(hb)
    session.commit()
    # session将在teardown_request中关闭
    return jsonify({'success': True})

# 在线人数接口
@app.route('/<name>/onlinecount')
def onlinecount(name):
    if not is_room_approved(name):
        return jsonify({'online': 0})
    session = get_db_session(name)

    threshold = datetime.utcnow() - timedelta(seconds=30)
    count = session.query(Heartbeat).filter_by(room=name).filter(Heartbeat.last_beat >= threshold).count()
    # session将在teardown_request中关闭
    return jsonify({'online': count})

# 聊天室页面
@app.route('/<name>/room')
def room(name):
    if is_room_approved(name):
        return render_template('room.html', room=name)

    if not app.config.get('REQUIRE_ROOM_CREATION_APPROVAL'):
        get_db_session(name) # This will create the room
        return render_template('room.html', room=name)
    
    user_session = get_user_db_session()
    pending_room = user_session.query(PendingRoom).filter_by(room_name=name).first()

    if not pending_room:
        new_pending_room = PendingRoom(room_name=name)
        user_session.add(new_pending_room)
        user_session.commit()

        try:
            admin_email = app.config.get('ADMIN_EMAIL')
            if admin_email:
                token_data = {'room_name': name}
                approve_token = s.dumps(token_data, salt='approve-room')
                deny_token = s.dumps(token_data, salt='deny-room')

                approve_url = url_for('approve_room', token=approve_token, _external=True)
                deny_url = url_for('deny_room', token=deny_token, _external=True)

                html_body = render_template(
                    'room_approval_email.html',
                    room_name=name,
                    approve_url=approve_url,
                    deny_url=deny_url
                )
                subject = f"请求创建新的聊天室: '{name}'"
                msg = MailMessage(subject, recipients=[admin_email], html=html_body)
                mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send room approval email: {e}")

    return render_template('pending_approval.html', room_name=name)


# 聊天历史接口：支持分页获取最新历史（默认）、获取since_id之后的新消息、获取before_id之前的历史
@app.route('/<name>/history')
def history(name):
    if not is_room_approved(name):
        return jsonify({'messages': [], 'total': 0})
    session = get_db_session(name)

    since_id = request.args.get('since_id', type=int)
    before_id = request.args.get('before_id', type=int)
    per_page = 10 # 每页数量

    if since_id is not None:
        # 获取since_id之后的新消息
        messages = session.query(Message).filter_by(room=name).filter(Message.id > since_id).order_by(Message.id.asc()).all()
        # session将在teardown_request中关闭
        return jsonify({
            'messages': [msg.to_dict() for msg in messages],
            'has_next': False, # 获取新消息时没有分页概念
            'has_prev': False,
            'total': len(messages)
        })
    elif before_id is not None:
        # 获取before_id之前的历史消息 (分页)
        query = session.query(Message).filter_by(room=name).filter(Message.id < before_id).order_by(Message.id.desc())
        # SQLAlchemy核心没有paginate方法，需要手动实现分页
        page = 1 # 对于before_id，总是获取第一页
        offset = (page - 1) * per_page
        messages = query.offset(offset).limit(per_page).all()
        # 判断是否有下一页和上一页需要额外的查询
        has_next = session.query(query.exists()).scalar() # 检查是否有更多小于before_id的消息
        has_prev = False # 获取before_id之前的历史时，没有“上一页”的概念，因为我们总是从before_id往前取

        # session将在teardown_request中关闭
        return jsonify({
            'messages': [msg.to_dict() for msg in messages],
            'has_next': has_next,
            'has_prev': has_prev,
            'total': session.query(Message).filter_by(room=name).filter(Message.id < before_id).count() # 获取总数
        })
    else:
        # 首次加载或分页获取最新历史消息 (倒序)
        try:
            page = int(request.args.get('page', 1))
        except:
            page = 1
        query = session.query(Message).filter_by(room=name).order_by(Message.id.desc())
        # SQLAlchemy核心没有paginate方法，需要手动实现分页
        offset = (page - 1) * per_page
        messages = query.offset(offset).limit(per_page).all()

        # 判断是否有下一页和上一页
        total_count = session.query(Message).filter_by(room=name).count()
        has_next = (offset + len(messages)) < total_count
        has_prev = page > 1

        # session将在teardown_request中关闭
        return jsonify({
            'messages': [msg.to_dict() for msg in messages],
            'has_next': has_next,
            'has_prev': has_prev,
            'total': total_count
        })

# 发送消息接口
@app.route('/<name>/send', methods=['POST'])
def send(name):
    if not is_room_approved(name):
        return jsonify({'success': False, 'error': 'Room not found or not approved'}), 404
    session = get_db_session(name)
    user_session = get_user_db_session()
    data = request.json
    nickname = data.get('nickname', '').strip()
    email = data.get('email', '').strip()
    content = data.get('content', '').strip()
    device_id = data.get('device_id', '').strip()

    if not (nickname and email and content and device_id):
        return jsonify({'success': False, 'error': '参数不完整'}), 400

    # --- Reply and Content Processing ---
    # Step 1: Find original authors to notify, using original content
    try:
        replied_to_ids = set(re.findall(r'#(\d+)#', content))
        authors_to_notify = []
        for msg_id in replied_to_ids:
            original_message = session.query(Message).filter_by(id=int(msg_id)).first()
            if original_message and original_message.email != email:
                authors_to_notify.append(original_message.email)
    except Exception as e:
        app.logger.error(f"Error finding reply authors: {e}")
        authors_to_notify = []

    # Step 2: Transform content for storage and display (replace #123# with HTML)
    processed_content = re.sub(r'#(\d+)#', r'<span style="color: blue;">#\1#</span>', content)

    # Step 3: Send reply notifications using the processed content
    if authors_to_notify:
        try:
            subject = f"您在聊天室 '{name}' 中有新的回复"
            # The markdown library will safely handle the HTML span tag
            reply_content_html = markdown.markdown(processed_content)
            room_url = url_for('room', name=name, _external=True)
            html_body = render_template(
                'reply_notification_email.html',
                room_name=name,
                replier_nickname=nickname,
                reply_content_html=reply_content_html,
                room_url=room_url
            )
            # Use set to avoid sending multiple emails to the same person if they are replied to multiple times
            mail_msg = MailMessage(subject, recipients=list(set(authors_to_notify)), html=html_body)
            mail.send(mail_msg)
        except Exception as e:
            app.logger.error(f"Failed to send reply notification email: {e}")


    verified_device = user_session.query(VerifiedDevice).filter_by(device_id=device_id).first()
    if not verified_device:
        token = s.dumps({'email': email, 'device_id': device_id, 'room': name}, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('verify_email.html', confirm_url=confirm_url)
        subject = "请确认您的新设备"
        msg = MailMessage(subject, recipients=[email], html=html)
        mail.send(msg)
        return jsonify({'success': False, 'error': '需要邮件验证', 'device_id': device_id}), 401

    msg = Message(room=name, nickname=nickname, email=email, content=processed_content) # Use processed content
    session.add(msg)
    session.commit()

    # Send notification email to admin if enabled
    if app.config.get('SEND_NOTIFICATION_EMAIL'):
        try:
            admin_email = app.config.get('ADMIN_EMAIL')
            if admin_email:
                subject = f"聊天室 '{name}' 有新消息"
                # Convert processed content from Markdown to HTML
                message_html = markdown.markdown(processed_content)
                room_url = url_for('room', name=name, _external=True)
                # Render the email template
                html_body = render_template(
                    'notification_email.html',
                    room_name=name,
                    nickname=nickname,
                    email=email,
                    message_html=message_html,
                    room_url=room_url
                )
                mail_msg = MailMessage(subject, recipients=[admin_email], html=html_body)
                mail.send(mail_msg)
        except Exception as e:
            # Log the error but don't block the user's request
            app.logger.error(f"Failed to send notification email: {e}")

    return jsonify({'success': True, 'message': msg.to_dict()})

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        data = s.loads(token, salt='email-confirm', max_age=3600)
        email = data['email']
        device_id = data['device_id']
        
        user_session = get_user_db_session()
        # Check if the device_id is already in the database, regardless of email.
        existing_device = user_session.query(VerifiedDevice).filter_by(device_id=device_id).first()
        if not existing_device:
            # If the device is not verified for any email, add it.
            new_device = VerifiedDevice(email=email, device_id=device_id)
            user_session.add(new_device)
            user_session.commit()

        return render_template('verification_success.html', token=token)
    except (SignatureExpired, BadTimeSignature):
        return "验证链接无效或已过期。"

@app.route('/approve_room/<token>')
def approve_room(token):
    user_session = get_user_db_session()
    try:
        data = s.loads(token, salt='approve-room', max_age=3600 * 24) # 24 hours to approve
        room_name = data['room_name']
        
        pending_room = user_session.query(PendingRoom).filter_by(room_name=room_name).first()
        if not pending_room:
            return render_template('room_creation_result.html', success=False, message="请求不存在或已处理。")

        if pending_room.status == 'approved':
            room_url = url_for('room', name=room_name, _external=True)
            return render_template('room_creation_result.html', success=True, message=f"聊天室 '{room_name}' 已被批准。", room_url=room_url)

        # Create the room database
        get_db_session(room_name, create_if_not_exist=True)
        
        pending_room.status = 'approved'
        user_session.commit()
        
        room_url = url_for('room', name=room_name, _external=True)
        return render_template('room_creation_result.html', success=True, message=f"聊天室 '{room_name}' 已成功创建。", room_url=room_url)

    except (SignatureExpired, BadTimeSignature):
        return render_template('room_creation_result.html', success=False, message="批准链接无效或已过期。")

@app.route('/deny_room/<token>')
def deny_room(token):
    user_session = get_user_db_session()
    try:
        data = s.loads(token, salt='deny-room', max_age=3600 * 24)
        room_name = data['room_name']

        pending_room = user_session.query(PendingRoom).filter_by(room_name=room_name).first()
        if not pending_room:
            return render_template('room_creation_result.html', success=False, message="请求不存在或已处理。")

        pending_room.status = 'denied'
        user_session.commit()
        
        return render_template('room_creation_result.html', success=True, message=f"已拒绝创建聊天室 '{room_name}'。")

    except (SignatureExpired, BadTimeSignature):
        return render_template('room_creation_result.html', success=False, message="拒绝链接无效或已过期。")


@app.route('/<name>/delete/<int:message_id>', methods=['POST'])
def delete_message(name, message_id):
    if not is_room_approved(name):
        return jsonify({'success': False, 'error': 'Room not found or not approved'}), 404
    session = get_db_session(name)
    user_session = get_user_db_session()
    msg = session.query(Message).filter_by(id=message_id, room=name).first()
    
    data = request.json
    admin_email = data.get('email', '').strip().lower()
    device_id = data.get('device_id', '').strip()
    verified_device = user_session.query(VerifiedDevice).filter_by(device_id=device_id, email=admin_email).first()
    
    if not verified_device :
        return jsonify({'success': False, 'error': '管理员设备未验证'}), 403
    
    elif (admin_email.lower() != msg.email.lower()) and (admin_email.lower() != config.ADMIN_EMAIL.lower()) :
        
        return jsonify({'success': False, 'error': '无权限'}), 403
    
    elif msg :
        session.delete(msg)
        session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '消息未找到'}), 404

# 静态文件路由
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    # 启动时不再需要创建全局的chatroom.db
    # 数据库会在第一次访问某个房间时自动创建
    app.run(debug=True,host="0.0.0.0", port=18765)
