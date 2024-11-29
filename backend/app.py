from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import server

app = Flask(__name__)

app.secret_key = "secret_key"

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

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
    print("Updating room list for", username)

    if username:
        room_list = server.get_room_list(username)
        socketio.emit('room_list_update', room_list, to=username)
    else:
        print("No username provided for room list update")

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=12345, debug=True)