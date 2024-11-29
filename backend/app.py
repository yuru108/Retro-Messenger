from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import server

app = Flask(__name__)
app.secret_key = "secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

connected_users = {}  # 已驗證用戶：{username: socket.id}
pending_connections = {}  # 暫時存儲尚未驗證的連線：{socket.id: True}

@socketio.on('connect')
def handle_connect():
    pending_connections[request.sid] = True
    print(f"Socket {request.sid} connected, waiting for authentication.")

@socketio.on('disconnect')
def handle_disconnect():
    sid_to_remove = request.sid
    # 從已驗證用戶中移除
    for username, sid in list(connected_users.items()):
        if sid == sid_to_remove:
            del connected_users[username]
            print(f"User {username} disconnected")
            break

    # 從待驗證連線中移除
    if sid_to_remove in pending_connections:
        del pending_connections[sid_to_remove]
        print(f"Socket {sid_to_remove} disconnected (not authenticated)")

@socketio.on('authenticate')
def handle_authentication(data):
    username = data.get('username')
    if username:
        if username in connected_users:
            return  # 用戶已經驗證過

        # 將用戶名綁定到 socket.id
        connected_users[username] = request.sid
        if request.sid in pending_connections:
            del pending_connections[request.sid]
        print(f"User {username} authenticated with Socket ID {request.sid}")
        socketio.emit('authenticated', {'status': 'success'}, to=request.sid)
    else:
        print(f"Authentication failed for socket {request.sid}")
        socketio.emit('authenticated', {'status': 'failed'}, to=request.sid)

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
    
    # 更新用戶的聊天室列表
    room_list_update(username)
    return jsonify({'message': "Login successful", 'username': username}), 200

@app.route('/logout', methods=['POST'])
def logout():
    """
    Logout the current user
    Response: { "message": "Logout successful" }
    """
    data = request.json
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    result = server.logout_user(username)
    
    if "logout_success" in result:
        # 更新用戶的聊天室列表
        room_list_update(username)

        return jsonify({'message': "Logout successful"}), 200

@app.route('/user-list', methods=['GET'])
def user_list():
    """
    Get the list of registered users
    Response: users = [ { "username": "username" }, ... ]
    """    
    result = server.get_user_list()
    return jsonify(result), 200

@app.route('/room-list', methods=['GET'])
def room_list():
    """
    Get the list of chat rooms
    Request: ?username=username
    Response: rooms = [ {"room_id": "room_id", "room_name": "room_name", "isOnline": True/False }, ... ]
    """
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    result = server.get_room_list(username)

    for room in result:
        room_id = room.get('room_id')
        members = server.get_room_members(room_id, username)
        online_members = [member for member in members if member in connected_users]
        room['isOnline'] = True if online_members else False

    return jsonify(result), 200

@app.route('/send-message', methods=['POST'])
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
        history_update(to_room_id, from_user)
        return jsonify({'status': 'Message sent'}), 200
    else:
        return jsonify({'status': 'Failed to send message'}), 500

@app.route('/message-history', methods=['GET'])
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
def create_room():
    """
    Create a new chat room
    Request body: { "room_name": "room_name", "userlist": ["username1", "username2", ...] }
    Response: { "room_id": "room_id" }
    """
    data = request.json
    room_name = data.get('room_name')
    userlist = data.get('userlist')

    if not all([room_name, userlist]):
        return jsonify({'error': 'Invalid data'}), 400
    
    result = server.create_room(room_name, userlist)
    return jsonify(result), 200

def room_list_update(username):
    """
    Push the updated room list to a specific user
    """
    if username:
        for user in connected_users:
            room_list = server.get_room_list(user)
            socketio.emit('room_list_update', room_list, to=connected_users[user])
            print(f"Room list updated for {user}")
    else:
        print("No username provided for room list update")

def history_update(room_id, username):
    """
    Push the updated message history to a specific user
    """
    if room_id and username:
        message = server.get_history(room_id, username)
        member_list = server.get_room_members(room_id, username)
        for member in member_list:
            if member in connected_users:
                socketio.emit('history_update', message, to=connected_users[member])
    else:
        print("No room ID or username provided for history update")

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=12345, debug=True)