import asyncio
import websockets
import sqlite3
from datetime import datetime
import bcrypt

conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS RoomMembers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES Rooms(room_id),
    FOREIGN KEY (username) REFERENCES Users(username)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Messages (
    id INTEGER PRIMARY KEY,
    from_user INTEGER,
  	to_room_id INTEGER,
    message TEXT,
    date TEXT,
  	"read" BOOLEAN DEFAULT 0,
    FOREIGN KEY (from_user) REFERENCES Users(username),
  	FOREIGN KEY (to_room_id) REFERENCES Rooms(room_id)
);
""")
conn.commit()

class User:
    def __init__(self, username, websocket):
        self.username = username
        self.websocket = websocket

class Room:
    def __init__(self, room_id, room_name):
        self.room_id = room_id
        self.room_name = room_name

class Message:
    def __init__(self, from_user, to_room_id, message):
        self.from_user = from_user
        self.to_room_id = to_room_id
        self.message = message
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.read = False

    async def format_message(self):
        from_user = await find_user_by_name(self.from_user)
        to_room = await find_room_by_roomid(self.to_room_id)
        return f"[{to_room.room_name}] {from_user.username}: {self.message} {self.date}({'已讀' if self.read else '未讀'})"

    def save_to_db(self):
        cursor.execute(
            "INSERT INTO Messages (from_user, to_room_id, message, date) VALUES (?, ?, ?, ?)",
            (self.from_user, self.to_room_id, self.message, self.date)
        )
        conn.commit()

connected_users = {}

async def get_unread_messages(user, room_id):
    cursor.execute(
        "SELECT from_user, message, date FROM Messages WHERE to_room_id = ? AND from_user != ? AND read = 0",
        (room_id, user.username)
    )
    message = cursor.fetchall()

    if message:
        for from_user, to_room_id, msg, date, read in message:
            from_user = await find_user_by_name(from_user)
            to_room = await find_room_by_roomid(to_room_id)
            response += f"{to_room.room_name} {from_user.username} {msg} {date} {'已讀' if read else '未讀'}\n"
    else:
        response = None

    await user.websocket.send(response)

async def mark_messages_as_read(room_id):
    cursor.execute(
        "UPDATE Messages SET read = 1 WHERE to_room_id = ? AND read = 0",
        (room_id,)
    )
    conn.commit()

async def find_user_by_name(username):
    cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        if connected_users.get(str(user[0])):
            return connected_users[str(user[0])]
        return User(user[0], None)
    return None

async def find_room_by_roomid(room_id):
    cursor.execute("SELECT * FROM Rooms WHERE room_id = ?", (room_id,))
    room = cursor.fetchone()
    if room:
        return Room(room[0], room[1])
    return None

async def register_user(websocket):
    """註冊新使用者並建立個人聊天室"""
    # 請求使用者名稱和密碼
    username = await websocket.recv()
    raw_password = await websocket.recv()
    hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

    # 檢查使用者是否已存在
    cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
    if cursor.fetchone():
        await websocket.send("user_already_exists")
        print(f"使用者名稱 {username} 已存在")
        return None

    # 新增使用者至資料庫
    cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    await websocket.send(f"註冊成功：{username}")
    print(f"註冊成功：{username}")

    # 為新使用者與所有現有使用者建立個人聊天室
    cursor.execute("SELECT username FROM Users WHERE username != ?", (username,))
    existing_users = cursor.fetchall()

    for existing_username in existing_users:
        room_name = f"{username} & {existing_username}"
        cursor.execute("INSERT INTO Rooms (room_name) VALUES (?)", (room_name,))
        room_id = cursor.lastrowid
        conn.commit()

        # 將新使用者與現有使用者加入房間
        cursor.execute("INSERT INTO RoomMembers (room_id, username) VALUES (?, ?)", (room_id, username))
        cursor.execute("INSERT INTO RoomMembers (room_id, username) VALUES (?, ?)", (room_id, existing_username))
        conn.commit()
        print(f"建立個人聊天室：{room_name} (房間 ID: {room_id})")

    return User(username, websocket)

async def login_user(websocket):
    username = await websocket.recv()
    raw_password = await websocket.recv()

    cursor.execute("SELECT username, password FROM Users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    if not user_data:
        await websocket.send("login_error")
        print(f"Username {username} 未註冊")
        return None
    
    username, stored_password = user_data
    
    if not bcrypt.checkpw(raw_password.encode('utf-8'), stored_password):
        await websocket.send("login_error")
        print(f"{username} 密碼錯誤")
        return None

    await websocket.send(username)
    print(f"{username} 已登入")
    return User(username, websocket)

async def send_history(user, room_id):
    cursor.execute(
        "SELECT from_user, to_room_id, message, date, read FROM Messages WHERE to_room_id = ?",
        (room_id, )
    )
    history = cursor.fetchall()
    response = ""

    if history:
        for from_user, to_room_id, msg, date, read in history:
            from_user = await find_user_by_name(from_user)
            to_room = await find_room_by_roomid(to_room_id)
            response += f"{to_room.room_name} {from_user.username} {msg} {date} {'已讀' if read else '未讀'}\n"
        
        await mark_messages_as_read(room_id)
    else:
        response = "無歷史訊息"

    await user.websocket.send(response)

async def get_user_list(user):
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    response = ""

    for username in users:
        if username in connected_users:
            response += f"{username} isOnline\n"
        else:
            response += f"{username}\n"

    await user.websocket.send(response)

async def get_room_list(user):
    cursor.execute("SELECT * FROM Rooms WHERE room_id IN (SELECT room_id FROM RoomMembers WHERE username = ?)", (user.username,))
    rooms = cursor.fetchall()
    response = ""

    for room_id, room_name in rooms:
        response += f"{room_id} {room_name}\n"

    await user.websocket.send(response)

async def handle_message(user):
    try:
        async for message in user.websocket:
            print(f"Received message from {user.username}: {message}")
            if message.startswith("send_message"):
                _, to_room_id, msg = message.split(" ", 2)
                if find_room_by_roomid(to_room_id):
                    message = Message(user.username, to_room_id, msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    message.save_to_db()
                    await user.websocket.send("訊息已發送")
                else:
                    await user.websocket.send("無效使用者。")
            elif message.startswith("get_messages_history"):
                _, room_id = message.split(" ")
                await send_history(user, room_id)
            elif message.startswith("get_unread_messages"):
                _, room_id = message.split(" ")
                await get_unread_messages(user, room_id)
            elif message == "get_user_list":
                await get_user_list(user)
            elif message == "get_room_list":
                await get_room_list(user)
    except websockets.ConnectionClosed:
        print(f"{user.username} 離線")
        connected_users.pop(user.username)

async def main(websocket):
    user = None
    try:
        # 註冊或登入邏輯
        operation = await websocket.recv()
        if operation == "register":
            user = await register_user(websocket)
        elif operation == "login":
            user = await login_user(websocket)
        else:
            await websocket.send("未知操作，連線結束")
            return

        if user:
            connected_users[user.username] = user
            await handle_message(user)
    except Exception as e:
        print(f"處理連線時發生錯誤: {e}")
    finally:
        # 清理已斷開的用戶
        if user and user.username in connected_users:
            del connected_users[user.username]
            print(f"用戶 {user.username} 已斷開連線")

async def websocket_server():
    """啟動 WebSocket 伺服器"""
    async with websockets.serve(main, "0.0.0.0", 8000, ping_interval=20, ping_timeout=10):
        print("伺服器已啟動，等待連線...")
        await asyncio.Future()  # 保持伺服器運行

if __name__ == "__main__":
    asyncio.run(websocket_server())