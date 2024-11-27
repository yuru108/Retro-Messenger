from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import asyncio
import websockets

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# WebSocket URI
WS_SERVER_URI = "ws://127.0.0.1:8000"

# Helper to send data to the WebSocket server
async def send_to_server(event, *args):
    try:
        async with websockets.connect(WS_SERVER_URI) as websocket:
            await websocket.send(event)
            for arg in args:
                await websocket.send(arg)
            response = []
            while True:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    response.append(msg)
                except asyncio.TimeoutError:
                    break
            return response
    except Exception as e:
        return [f"Error: {str(e)}"]

# API routes
@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Request body: { "username": "username", "password": "password" }
    Response: { "message": "Registration successful", "uid": "user_id" }
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    result = asyncio.run(send_to_server("register", username, password))
    if "user_already_exists" in result:
        return jsonify({'message': "User already exists"}), 400
    return jsonify({'message': "Registration successful", 'uid': result[0]})

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

    result = asyncio.run(send_to_server("login", username, password))
    if "login_error" in result:
        return jsonify({'message': "Login failed"}), 401
    return jsonify({'message': "Login successful", 'username': result[0]})

@app.route('/user-list', methods=['GET'])
def user_list():
    """
    Get the list of registered users
    Response: users = [ { "uid": "user_id", "username": "username", "isOnline": true/false }, ... ]
    """
    result = asyncio.run(send_to_server("get_user_list"))
    users = []
    for user in result:
        parts = user.split()
        users.append({'uid': parts[0], 'username': parts[1], 'isOnline': parts[-1] == "isOnline"})
    return jsonify(users)

@app.route('/room-list', methods=['GET'])
def room_list():
    """
    Get the list of chat rooms
    Request: ?username=username
    Response: rooms = [ { "room_id": "room_id", "room_name": "room_name" }, ... ]
    """
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'UID is required'}), 400

    result = asyncio.run(send_to_server("get_room_list", uid))
    rooms = []
    for room in result:
        parts = room.split()
        rooms.append({'room_id': parts[0], 'room_name': parts[1]})
    return jsonify(rooms)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    from_uid = data.get('from_uid')
    to_room_id = data.get('to_room_id')
    message = data.get('message')

    if not all([from_uid, to_room_id, message]):
        return jsonify({'error': 'Invalid data'}), 400

    result = asyncio.run(send_to_server("send_message", from_uid, to_room_id, message))
    return jsonify({'status': "Message sent" if "訊息已發送" in result else "Failed to send message"})

@app.route('/message-history', methods=['GET'])
def history():
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({'error': 'Room ID is required'}), 400

    result = asyncio.run(send_to_server("get_messages_history", room_id))
    messages = []
    for message in result:
        parts = message.split()
        messages.append({
            'room_name': parts[0],
            'from_user': parts[1],
            'message': parts[2],
            'date': parts[3],
            'status': parts[4] == "已讀"
        })
    return jsonify(messages)

@app.route('/unread-messages', methods=['GET'])
def unread_messages():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    result = asyncio.run(send_to_server("get_unread_messages", uid))
    messages = []
    for message in result:
        parts = message.split()
        messages.append({
            'room_name': parts[0],
            'from_user': parts[1],
            'message': parts[2],
            'date': parts[3],
            'status': parts[4] == "已讀"
        })
    return jsonify(messages)

# WebSocket events for real-time communication
@socketio.on('connect')
def handle_connect():
    print('Web client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Web client disconnected')

# Run the Flask-SocketIO server
if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)