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
    from_user TEXT,
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
    def __init__(self, username):
        self.username = username

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

def mark_messages_as_read(room_id, username):
    cursor.execute(
        "UPDATE Messages SET read = 1 WHERE to_room_id = ? AND from_user != ? AND read = 0",
        (username, room_id,)
    )
    conn.commit()

def find_user_by_name(username):
    cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        return User(user[0])
    return None

def find_room_by_roomid(room_id):
    cursor.execute("SELECT * FROM Rooms WHERE room_id = ?", (room_id,))
    room = cursor.fetchone()
    if room:
        return Room(room[0], room[1])
    return None

def register_user(username, password):
    """註冊新使用者並建立個人聊天室"""
    # 請求使用者名稱和密碼
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 檢查使用者是否已存在
    cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"使用者名稱 {username} 已存在")
        return "user_already_exists"

    # 新增使用者至資料庫
    cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    print(f"註冊成功：{username}")

    # 為新使用者與所有現有使用者建立個人聊天室
    cursor.execute("SELECT username FROM Users WHERE username != ?", (username,))
    existing_users = cursor.fetchall()

    for existing_username in existing_users:
        existing_username = existing_username[0]
        room_name = f"{username} & {existing_username}"
        
        cursor.execute("INSERT INTO Rooms (room_name) VALUES (?)", (room_name,))
        room_id = cursor.lastrowid
        conn.commit()

        cursor.execute("INSERT INTO RoomMembers (room_id, username) VALUES (?, ?)", (room_id, username))
        cursor.execute("INSERT INTO RoomMembers (room_id, username) VALUES (?, ?)", (room_id, existing_username))
        conn.commit()

        print(f"建立個人聊天室： {room_name}")
    return "register_success"

def login_user(username, password):
    """使用者登入"""
    cursor.execute("SELECT username, password FROM Users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    if not user_data:
        print(f"Username {username} 未註冊")
        return "login_error"
    
    username, stored_password = user_data
    
    if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        print(f"{username} 密碼錯誤")
        return "login_error"

    print(f"{username} 已登入")
    return username

def get_history(room_id, username):
    cursor.execute(
        "SELECT from_user, to_room_id, message, date, read FROM Messages WHERE to_room_id = ?",
        (room_id, )
    )
    history = cursor.fetchall()
    response = []

    if history:
        for from_user, to_room_id, msg, date, read in history:
            from_user = find_user_by_name(from_user)
            to_room = find_room_by_roomid(to_room_id)
            response.append({
                "room_name": to_room.room_name,
                "from_user": from_user.username,
                "message": msg,
                "date": date,
                "status": True if read else False
            })
        mark_messages_as_read(room_id, username)
    else:
        response = {"message": "no_messages"}

    return response

def get_user_list():
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    response = []

    for username in users:
        username = username[0]
        response.append({
            "username": username,
            "isOnline": None
        })
    
    return response

def get_room_list(username):
    cursor.execute("SELECT * FROM Rooms WHERE room_id IN (SELECT room_id FROM RoomMembers WHERE username = ?)", (username,))
    rooms = cursor.fetchall()
    response = []

    for room_id, room_name in rooms:
        response.append({
            "room_id": room_id,
            "room_name": room_name
        })

    return response

def get_unread_messages(username):
    cursor.execute(
        "SELECT from_user, to_room_id, message, date, read FROM Messages WHERE to_room_id IN (SELECT room_id FROM RoomMembers WHERE username = ?) AND read = 0",
        (username, )
    )
    messages = cursor.fetchall()
    response = []

    if messages:
        for from_user, to_room_id, msg, date, read in messages:
            from_user = find_user_by_name(from_user)
            to_room = find_room_by_roomid(to_room_id)
            response.append({
                "room_name": to_room.room_name,
                "from_user": from_user.username,
                "message": msg,
                "date": date,
                "status": True if read else False
            })
    else:
        response = {"message": "no_messages"}

    return response

def send_message(from_user, to_room_id, message):
    if find_room_by_roomid(to_room_id):
        message_obj = Message(from_user, to_room_id, message)
        message_obj.save_to_db()
        return "message_sent"
    else:
        return "message_failed"

def create_room(room_name, *users):
    cursor.execute("INSERT INTO Rooms (room_name) VALUES (?)", (room_name,))
    room_id = cursor.lastrowid
    conn.commit()

    for username in users:
        cursor.execute("INSERT INTO RoomMembers (room_id, username) VALUES (?, ?)", (room_id, username))
        conn.commit()

    return room_id
    
def change_room_name(room_id, new_name):
    cursor.execute("SELECT * FROM Rooms WHERE room_id = ?", (room_id,))
    room = cursor.fetchone()
    if not room:
        return "room_not_found"

    cursor.execute("UPDATE Rooms SET room_name = ? WHERE room_id = ?", (new_name, room_id))
    conn.commit()

    return "room_name_changed"