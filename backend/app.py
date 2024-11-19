import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import hashlib
import uuid
from datetime import datetime

# 初始化 Flask 應用程式並啟用跨域請求支持
app = Flask(__name__)
CORS(app)

# 使用者資料儲存（僅在記憶體中，重啟後會清除）
users = {}

# 消息歷史記錄結構（僅供參考，部分記錄儲存在 SQLite 資料庫中）
message_history = {}

# 連接 SQLite 資料庫
def get_db_connection():
    """
    建立並返回 SQLite 資料庫的連線物件。
    """
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row  # 使返回的結果以字典形式表示
    return conn

# 初始化 SQLite 資料庫並創建所需資料表
def init_db():
    """
    初始化資料庫，創建 messages 資料表以儲存聊天記錄。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_uid TEXT NOT NULL,
            to_uid TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 啟動應用程式時初始化資料庫
init_db()

# 密碼雜湊處理
def hash_password(password):
    """
    使用 SHA-256 將密碼進行不可逆的雜湊處理。
    """
    return hashlib.sha256(password.encode()).hexdigest()

# 註冊新使用者
@app.route('/register', methods=['POST'])
def register():
    """
    處理使用者註冊請求。
    接受參數：username 和 password。
    返回：成功註冊的 UID。
    """
    data = request.json
    uid = str(uuid.uuid4())  # 為每位新使用者產生唯一 UID
    username = data.get('username')
    password = data.get('password')

    # 檢查所需欄位
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # 檢查使用者名稱是否已被註冊
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409

    # 儲存新使用者資訊
    users[username] = {
        'uid': uid,
        'username': username,
        'password': hash_password(password),
        'isOnline': False,
    }

    return jsonify({'message': 'Registration successful', 'uid': uid}), 201

# 使用者登入
@app.route('/login', methods=['POST'])
def login():
    """
    處理使用者登入請求。
    接受參數：username 和 password。
    返回：成功登入的 UID。
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 檢查所需欄位
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # 確認使用者是否存在及密碼是否正確
    user = users.get(username)
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # 更新狀態為上線
    user['isOnline'] = True
    return jsonify({'message': 'Login successful', 'uid': user['uid']}), 200

# 獲取使用者清單
@app.route('/user-list', methods=['GET'])
def get_user_list():
    """
    返回所有已註冊使用者的清單。
    包括 UID、使用者名稱以及線上狀態。
    """
    user_list = [{'uid': user['uid'], 'username': user['username'], 'isOnline': user['isOnline']} for user in users.values()]
    return jsonify(user_list)

# 傳送消息
@app.route('/send-message', methods=['POST'])
def send_message():
    """
    接收並儲存一條消息。
    接受參數：from_uid、to_uid、message。
    返回：成功狀態。
    """
    data = request.json
    from_uid = data.get('from')
    to_uid = data.get('to')
    message = data.get('message')

    # 驗證是否有足夠的資料
    if not from_uid or not to_uid or not message:
        return jsonify({'error': 'Invalid data'}), 400

    # 儲存消息到資料庫
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (from_uid, to_uid, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (from_uid, to_uid, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    return jsonify({'status': 'Message sent successfully'}), 200

# 獲取聊天歷史記錄
@app.route('/message-history', methods=['GET'])
def get_message_history():
    """
    返回指定雙方的聊天記錄。
    接受參數：from_uid 和 to_uid。
    返回：雙方之間的所有消息記錄。
    """
    to_uid = request.args.get('to_uid')
    from_uid = request.args.get('from_uid')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM messages WHERE (from_uid = ? AND to_uid = ?) OR (from_uid = ? AND to_uid = ?)',
        (from_uid, to_uid, to_uid, from_uid)
    )
    messages = cursor.fetchall()
    conn.close()

    # 將結果轉為 JSON 格式
    message_list = [
        {'from_uid': msg['from_uid'], 'to_uid': msg['to_uid'], 'message': msg['message'], 'timestamp': msg['timestamp']}
        for msg in messages
    ]
    return jsonify(message_list)

# 更新使用者狀態
@app.route('/update-status', methods=['POST'])
def update_status():
    """
    更新指定使用者的線上狀態。
    接受參數：uid 和 isOnline。
    返回：成功或錯誤訊息。
    """
    data = request.json
    uid = data.get('uid')
    is_online = data.get('isOnline')

    # 更新使用者的線上狀態
    for user in users.values():
        if user['uid'] == uid:
            user['isOnline'] = is_online
            return jsonify({'status': 'Status updated successfully'}), 200

    return jsonify({'error': 'User not found'}), 404

# 啟動應用程式
if __name__ == '__main__':
    app.run(port=12345)
