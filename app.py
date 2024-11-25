import asyncio
from threading import Thread
from flask import Flask, jsonify, request
from flask_cors import CORS
import client

app = Flask(__name__)
CORS(app)

websocket = None

user = {
    'uid': None,
    'username': None
}

# 註冊新使用者
@app.route('/register', methods=['POST'])
def register():
    """
    處理使用者註冊請求。
    接受參數：username 和 password。
    返回：message(User already exists/Registration successful) 和成功註冊的 UID。
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 檢查所需欄位
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.register(websocket, user['username']))

    if 'uid' in result:
        user['uid'] = result['uid']
        user['username'] = result['username']

    return jsonify(result)

# 使用者登入
@app.route('/login', methods=['POST'])
def login():
    """
    處理使用者登入請求。
    接受參數：username 和 password。
    返回：message(login_error/Login successful) 和成功登入的 UID。
    """
    data = request.json
    uid = data.get('uid')
    password = data.get('password')

    # 檢查所需欄位
    if not uid or not password:
        return jsonify({'error': 'Uid and password are required'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.login(websocket, uid))

    if 'uid' in result:
        user['uid'] = result['uid']
        user['username'] = result['username']

    return jsonify(result)

# 獲取使用者清單
@app.route('/user-list', methods=['GET'])
def user_list():
    """
    獲取所有使用者清單。
    返回：使用者清單 result[] = {uid, username, isOnline}。
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.get_user_list(websocket))
    return jsonify(result)

@app.route('/room-list', methods=['GET'])
def room_list():
    """
    獲取使用者的房間清單。
    接受參數：uid。
    返回：房間清單 result[] = {room_id, room_name}。
    """
    uid = request.args.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.get_room_list(websocket))
    return jsonify(result)

@app.route('/send-message', methods=['POST'])
def send_message():
    """
    發送訊息至指定房間。
    接受參數：from_uid, to_room_id, message。
    返回：True/False。
    """
    data = request.json
    from_uid = data.get('from_uid')
    to_room_id = data.get('to_room_id')
    message = data.get('message')

    if not all([from_uid, to_room_id, message]):
        return jsonify({'error': 'Invalid data'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.send_message(websocket, from_uid, to_room_id, message))
    return jsonify({'status': result})

@app.route('/message-history', methods=['GET'])
def history():
    """
    獲取指定房間的歷史訊息。
    ("會"將獲取到的訊息標為已讀)
    接受參數：room_id。
    返回：歷史訊息 result[] = {from_uid, to_room_id, message, date, read(True/False)}。
    """
    room_id = request.args.get('room_id')
    if not room_id:
        return jsonify({'error': 'Room ID is required'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.get_message_history(websocket, room_id))
    return jsonify(result)

@app.route('/unread-messages', methods=['GET'])
def unread_messages():
    """
    獲取指定使用者的所有未讀訊息。
    ("不會"將獲取到的訊息標為已讀)
    接受參數：uid。
    返回：未讀訊息 result[] = {from_uid, to_room_id, message, date, read(True/False)}。
    """
    uid = request.args.get('uid')
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.get_unread_messages(websocket, uid))
    return jsonify(result)

def start_flask():
    """啟動 Flask 應用程式"""
    app.run(port=5000, threaded=True)

async def start_client_connection():
    """啟動 WebSocket 連線"""
    global websocket
    websocket = await client.create_connection()

if __name__ == '__main__':
    # 啟動 WebSocket 連線
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_client_connection())

    # 啟動 Flask 應用程式
    flask_thread = Thread(target=start_flask)
    flask_thread.start()
