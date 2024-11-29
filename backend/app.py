from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import server

app = Flask(__name__)
# 設置 session cookie 的名稱

from datetime import timedelta

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 設定 session 有效期為7天

app.config['SESSION_COOKIE_NAME'] = 'session'

# 設置 cookie 是否只能通過 HTTPS 傳送（開發環境中可以設為 False）
app.config['SESSION_COOKIE_SECURE'] = False  # 需要 HTTPS 時設為 True
app.config['SECRET_KEY'] = 'SecretKey'
# app.secret_key = "SecretKey"
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

active_connections = {}

@socketio.on('connect')
def on_connect():
    username = session.get('username')
    if username:
        active_connections[username] = request.sid
        print(f"User {username} connected with SID {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    for username, sid in list(active_connections.items()):
        if sid == request.sid:
            del active_connections[username]
            print(f"User {username} disconnected")
            break

# API routes
@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Request body: { "username": "username", "password": "password" }
    Response: { "message": "Registration successful", "username": "username" }
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    result = server.register_user(username, password)
    if "user_already_exists" in result:
        return jsonify({'error': "Username already exists"}), 409
    
    return jsonify({'message': "Registration successful", 'username': username}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Login an existing user
    Request body: { "username": "username", "password": "password" }
    Response: { "message": "Login successful", "username": "username" }
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    result = server.login_user(username, password)
    if "login_error" in result:
        return jsonify({'error': "Invalid username or password"}), 401
    
    session['username'] = username
    print(f"User {username} logged in. Session: {session}")  # 確認登錄後的 session
    return jsonify({'message': "Login successful", 'username': result[0]}), 200

@app.route('/logout', methods=['POST'])
def logout():
    """
    Logout the current user
    Response: { "message": "Logout successful" }
    """
    if 'username' not in session:
        return jsonify({'error': 'No active session'}), 400

    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    if username and username == session['username']:
        session.pop('username', None)
        print(f"User {username} logged out and disconnected")
        return jsonify({'message': "Logout successful"}), 200

@socketio.on('get_user_list')
def user_list():
    """
    Get the list of registered users
    Response: users = [ { "username": "username", "isOnline": "online/offline" }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    result = server.get_user_list()

    for user in result:
        if user['username'] in active_connections:
            user['isOnline'] = 'online'
        else:
            user['isOnline'] = 'offline'

    emit('user_list_response', {'status': 'success', 'users': result})

@socketio.on('get_room_list')
def room_list():
    """
    Get the list of chat rooms
    Request: ?username=username
    Response: rooms = [ {"room_id": "room_id", "room_name": "room_name" }, ... ]
    """
    print(f"Session: {session}")  # 打印 session 內容，檢查是否包含 'username'

    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    result = server.get_room_list(username)
    emit('room_list_response', {'status': 'success', 'rooms': result})

@socketio.on('send_message')
def send_message():
    """
    Send a message to a chat room
    Request body: { "username": "username", "to_room_id": "room_id", "message": "message" }
    Response: { "status": "Message sent" or "Failed to send message" }
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    data = request.json
    from_user = data.get('username')
    to_room_id = data.get('to_room_id')
    message = data.get('message')

    if not all([from_user, to_room_id, message]):
        return jsonify({'error': 'Invalid data'}), 400

    result = server.send_message(from_user, to_room_id, message)
    if result == "message_sent":
        emit('message_response', {'status': 'Message sent'}, broadcast=True)
    else:
        emit('message_response', {'status': 'Failed to send message'})

@socketio.on('get_message_history')
def history():
    """
    Get the message history of a chat room
    Request: ?room_id=room_id&username=username
    Response: result = [ { "room_name": "room_name", "from_user": "username", "message": "message", "date": "date", "status": true/false }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    room_id = request.args.get('room_id')
    username = request.args.get('username')
    if not room_id or not username:
        return jsonify({'error': 'Room ID and username is required'}), 400

    result = server.get_history(room_id, username)
    emit('message_history_response', {'status': 'success', 'history': result})

@socketio.on('unread_messages')
def unread_messages():
    """
    Get the unread messages of a user
    Request: ?username=username
    Response: messages = [ { "room_name": "room_name", "from_user": "username", "message": "message", "date": "date", "status": true/false }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'username is required'}), 400

    result = server.get_unread_messages(username)
    return jsonify(result)

@socketio.on('change_room_name')
def change_room_name():
    """
    Change the name of a chat room
    Request body: { "room_id": "room_id", "room_name": "room_name" }
    Response: { "status": "Room name changed" or "Failed to change room name" }
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    data = request.json
    room_id = data.get('room_id')
    room_name = data.get('room_name')

    if not all([room_id, room_name]):
        return jsonify({'error': 'Invalid data'}), 400

    result = server.change_room_name(room_id, room_name)
    if result == "room_name_changed":
        emit('change_room_name_response', {'message': 'Room name changed'}, broadcast=True)
    else:
        emit('change_room_name_response', {'message': 'Failed to change room name'})

@socketio.on('create_room')
def create_room():
    """
    Create a new chat room
    Request body: { "room_name": "room_name", "userlisr": ["username1", "username2", ...] }
    Response: { "status": "Room created" or "Failed to create room", "room_id": "room_id" }
    """

    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    data = request.json
    room_name = data.get('room_name')
    userlist = data.get('userlist')

    if not all([room_name, userlist]):
        return jsonify({'error': 'Invalid data'}), 400
    
    result = server.create_room(room_name, userlist)
    if "room_created" in result:
        emit('create_room_response', {'message': 'Room created', 'room_id': result['room_id']}, broadcast=True)
    else:
        emit('create_room_response', {'message': 'Failed to create room'})

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=12345, debug=True)