from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO
import server

app = Flask(__name__)
app.secret_key = "SecretKey"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    
    session['username'] = username
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
    return jsonify({'message': "Login successful", 'username': username}), 200

@app.route('/user-list', methods=['GET'])
def user_list():
    """
    Get the list of registered users
    Response: users = [ { "username": "username", "isOnline": true/false }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    result = server.get_user_list()
    return jsonify(result)

@app.route('/room-list', methods=['GET'])
def room_list():
    """
    Get the list of chat rooms
    Request: ?username=username
    Response: rooms = [ {"room_id": "room_id", "room_name": "room_name" }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    result = server.get_room_list(username)
    return jsonify(result)

@app.route('/send-message', methods=['POST'])
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
    if "message_sent" in result:
        return jsonify({'status': "Message sent"}), 200
    return jsonify({'status': "Failed to send message"}), 400

@app.route('/message-history', methods=['GET'])
def history():
    """
    Get the message history of a chat room
    Request: ?room_id=room_id&username=username
    Response: messages = [ { "room_name": "room_name", "from_user": "username", "message": "message", "date": "date", "status": true/false }, ... ]
    """
    if 'username' not in session:
        return jsonify({'error': 'Please login first'}), 401

    room_id = request.args.get('room_id')
    username = request.args.get('username')
    if not room_id or not username:
        return jsonify({'error': 'Room ID and username is required'}), 400

    result = server.get_history(room_id, username)
    return jsonify(result)

@app.route('/unread-messages', methods=['GET'])
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

@app.route('/change-room-name', methods=['POST'])
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
    if "room_name_changed" in result:
        return jsonify({'status': "Room name changed"}), 200
    return jsonify({'status': "Failed to change room name"}), 400

# WebSocket events for real-time communication
@socketio.on('connect')
def handle_connect():
    print('Web client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Web client disconnected')

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=12345, debug=True)