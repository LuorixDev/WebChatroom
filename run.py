from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import g # 导入g对象

app = Flask(__name__)
CORS(app)

# 定义数据库模型
Base = declarative_base()

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

# 动态获取数据库会话
# 动态获取数据库会话
def get_db_session(room_name):
    # 检查g对象是否已经存在session
    if 'db_session' not in g:
        db_dir = 'instance'
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join(db_dir, f'{room_name}.db')
        db_uri = f'sqlite:///{db_path}'
        engine = create_engine(db_uri)
        Base.metadata.create_all(engine) # 确保表存在
        Session = sessionmaker(bind=engine)
        g.db_session = Session() # 将session存储在g对象中
    return g.db_session

# 在请求结束后关闭数据库会话
@app.teardown_request
def remove_session(exception=None):
    # 从g对象获取session，如果存在则关闭
    session = g.pop('db_session', None)
    if session is not None:
        session.close()


# 心跳包接口
@app.route('/<name>/heartbeat', methods=['POST'])
def heartbeat(name):
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
    session = get_db_session(name)

    threshold = datetime.utcnow() - timedelta(seconds=30)
    count = session.query(Heartbeat).filter_by(room=name).filter(Heartbeat.last_beat >= threshold).count()
    # session将在teardown_request中关闭
    return jsonify({'online': count})

# 聊天室页面
@app.route('/<name>/room')
def room(name):
    # 这个路由不直接访问数据库，所以不需要获取session
    return render_template('room.html', room=name)

# 聊天历史接口：支持分页获取最新历史（默认）、获取since_id之后的新消息、获取before_id之前的历史
@app.route('/<name>/history')
def history(name):
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
    session = get_db_session(name)

    data = request.json
    nickname = data.get('nickname', '').strip()
    email = data.get('email', '').strip()
    content = data.get('content', '').strip()
    if not (nickname and email and content):
        # session将在teardown_request中关闭，这里不需要提前关闭
        return jsonify({'success': False, 'error': '参数不完整'}), 400

    msg = Message(room=name, nickname=nickname, email=email, content=content)
    session.add(msg)
    session.commit()
    # session将在teardown_request中关闭
    return jsonify({'success': True, 'message': msg.to_dict()})

# 静态文件路由
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    # 启动时不再需要创建全局的chatroom.db
    # 数据库会在第一次访问某个房间时自动创建
    app.run(debug=True,host="0.0.0.0", port=18765)
