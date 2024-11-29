from functools import wraps
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO
import server

app = Flask(__name__)

app.secret_key = "secret_key"

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False  # 若使用 HTTPS，則設為 True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 設定 session 有效期為 1 小時

CORS(app, supports_credentials=True, resources={
    r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}
})
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'error': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated_function

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
    return jsonify({'message': "Login successful", 'username': username}), 200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout the current user
    Response: { "message": "Logout successful" }
    """
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    if username and username == session['username']:
        session.pop('username', None)
        print(f"User {username} logged out and disconnected")
        return jsonify({'message': "Logout successful"}), 200

@app.route('/user-list', methods=['GET'])
@login_required
def user_list():
    """
    Get the list of registered users
    Response: users = [ { "username": "username", "isOnline": "online/offline" }, ... ]
    """    
    result = server.get_user_list()

    for user in result:
        if user['username'] in active_connections:
            user['isOnline'] = 'online'
        else:
            user['isOnline'] = 'offline'

    return jsonify(result), 200

@app.route('/room-list', methods=['GET'])
@login_required
def room_list():
    """
    Get the list of chat rooms
    Request: ?username=username
    Response: rooms = [ {"room_id": "room_id", "room_name": "room_name" }, ... ]
    """
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    result = server.get_room_list(username)
    return jsonify(result), 200

@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """
    Send a message to a chat room
    Request body: { "username": "username", "to_room_id": "room_id", "message": "message" }
    Response: { "status": "Message sent" or "Failed to send message" }
    """
    data = request.json
    from_user = data.get('username')
    to_room_id = data.get('to_room_id')
    message = data.get('message')

    if not all([from_user, to_room_id, message]):
        return jsonify({'error': 'Invalid data'}), 400

    result = server.send_message(from_user, to_room_id, message)
    if result == "message_sent":
        return jsonify({'status': 'Message sent'}), 200
    else:
        return jsonify({'status': 'Failed to send message'}), 500

@app.route('/message-history', methods=['GET'])
@login_required
def history():
    """
    Get the message history of a chat room
    Request: ?room_id=room_id&username=username
    Response: result = [ { "room_name": "room_name", "from_user": "username", "message": "message", "date": "date", "status": true/false }, ... ]
    """
    room_id = request.args.get('room_id')
    username = request.args.get('username')
    if not room_id or not username:
        return jsonify({'error': 'Room ID and username is required'}), 400

    result = server.get_history(room_id, username)
    return jsonify(result), 200

@app.route('/unread-messages', methods=['GET'])
@login_required
def unread_messages():
    """
    Get the unread messages of a user
    Request: ?username=username
    Response: messages = [ { "room_name": "room_name", "from_user": "username", "message": "message", "date": "date", "status": true/false }, ... ]
    """
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'username is required'}), 400

    result = server.get_unread_messages(username)
    return jsonify(result), 200

@app.route('/change-room-name', methods=['POST'])
@login_required
def change_room_name():
    """
    Change the name of a chat room
    Request body: { "room_id": "room_id", "room_name": "room_name" }
    Response: { "status": "Room name changed" or "Failed to change room name" }
    """
    data = request.json
    room_id = data.get('room_id')
    room_name = data.get('room_name')

    if not all([room_id, room_name]):
        return jsonify({'error': 'Invalid data'}), 400

    result = server.change_room_name(room_id, room_name)
    if result == "room_name_changed":
        return jsonify({'status': 'Room name changed'}), 200
    else:
        return jsonify({'status': 'Failed to change room name'}), 500

@app.route('/create-room', methods=['POST'])
@login_required
def create_room():
    """
    Create a new chat room
    Request body: { "room_name": "room_name", "userlisr": ["username1", "username2", ...] }
    Response: { "room_id": "room_id" }
    """
    data = request.json
    room_name = data.get('room_name')
    userlist = data.get('userlist')

    if not all([room_name, userlist]):
        return jsonify({'error': 'Invalid data'}), 400
    
    result = server.create_room(room_name, userlist)
    return jsonify(result), 200

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=12345, debug=True)