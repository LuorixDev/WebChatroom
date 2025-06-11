from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatroom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据库模型
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(64), index=True)
    nickname = db.Column(db.String(64))
    email = db.Column(db.String(128))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'room': self.room,
            'nickname': self.nickname,
            'email': self.email,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

# 心跳模型
class Heartbeat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(64), index=True)
    client_id = db.Column(db.String(64), index=True)
    last_beat = db.Column(db.DateTime, default=datetime.utcnow)

# 心跳包接口
@app.route('/<name>/heartbeat', methods=['POST'])
def heartbeat(name):
    data = request.json
    client_id = data.get('client_id', '').strip()
    if not client_id:
        return jsonify({'success': False, 'error': '缺少client_id'}), 400
    hb = Heartbeat.query.filter_by(room=name, client_id=client_id).first()
    now = datetime.utcnow()
    if hb:
        hb.last_beat = now
    else:
        hb = Heartbeat(room=name, client_id=client_id, last_beat=now)
        db.session.add(hb)
    db.session.commit()
    return jsonify({'success': True})

# 在线人数接口
@app.route('/<name>/onlinecount')
def onlinecount(name):
    threshold = datetime.utcnow() - timedelta(seconds=30)
    count = Heartbeat.query.filter_by(room=name).filter(Heartbeat.last_beat >= threshold).count()
    return jsonify({'online': count})



# 聊天室页面
@app.route('/<name>/room')
def room(name):
    return render_template('room.html', room=name)

# 聊天历史分页接口（倒序，每页10条）
@app.route('/<name>/history')
def history(name):
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
    per_page = 10
    query = Message.query.filter_by(room=name).order_by(Message.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    messages = [msg.to_dict() for msg in pagination.items]
    return jsonify({
        'messages': messages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'total': pagination.total
    })

# 发送消息接口
@app.route('/<name>/send', methods=['POST'])
def send(name):
    data = request.json
    nickname = data.get('nickname', '').strip()
    email = data.get('email', '').strip()
    content = data.get('content', '').strip()
    if not (nickname and email and content):
        return jsonify({'success': False, 'error': '参数不完整'}), 400
    msg = Message(room=name, nickname=nickname, email=email, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True, 'message': msg.to_dict()})

# 静态文件路由
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    if not os.path.exists('chatroom.db'):
        with app.app_context():
            db.create_all()
    # 确保心跳表存在
    with app.app_context():
        db.create_all()
    app.run(debug=True,host="0.0.0.0", port=18765)
