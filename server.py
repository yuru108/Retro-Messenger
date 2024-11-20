import asyncio
import websockets
import sqlite3
from datetime import datetime

conn = sqlite3.connect('chat.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Users (
    uid INTEGER PRIMARY KEY,
    username TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_uid INTEGER,
    to_uid INTEGER,
    message TEXT,
    date TEXT,
    read BOOLEAN DEFAULT 0,
    FOREIGN KEY (from_uid) REFERENCES Users(uid),
    FOREIGN KEY (to_uid) REFERENCES Users(uid)
)
""")
conn.commit()

class User:
    def __init__(self, uid, username, websocket):
        self.uid = uid
        self.username = username
        self.websocket = websocket

class Message:
    def __init__(self, from_uid, to_uid, message):
        self.from_uid = from_uid
        self.to_uid = to_uid
        self.message = message
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.read = False

    async def format_message(self):
        from_user = await find_user_by_uid(self.from_uid)
        to_user = await find_user_by_uid(self.to_uid)
        return f"[{self.date}] {from_user.username} -> {to_user.username}: {self.message} ({'已讀' if self.read else '未讀'})"

    def save_to_db(self):
        cursor.execute(
            "INSERT INTO Messages (from_uid, to_uid, message, date) VALUES (?, ?, ?, ?)",
            (self.from_uid, self.to_uid, self.message, self.date)
        )
        conn.commit()

connected_users = {}

async def get_unread_messages(uid):
    cursor.execute(
        "SELECT from_uid, message, date FROM Messages WHERE to_uid = ? AND read = 0",
        (uid,)
    )
    return cursor.fetchall()

async def mark_messages_as_read(uid):
    cursor.execute(
        "UPDATE Messages SET read = 1 WHERE to_uid = ? AND read = 0",
        (uid,)
    )
    conn.commit()

async def find_user_by_uid(uid):
    cursor.execute("SELECT * FROM Users WHERE uid = ?", (uid,))
    user = cursor.fetchone()
    if user:
        if connected_users.get(str(user[0])):
            return connected_users[str(user[0])]
        return User(user[0], user[1], None)
    return None

async def register_user(websocket):
    await websocket.send("請輸入uid:")
    uid = await websocket.recv()

    cursor.execute("SELECT username FROM Users WHERE uid = ?", (uid,))
    username = cursor.fetchone()

    if username:
        username = username[0]
        print(f"{username} ({uid}) logged in")
        await websocket.send(username)
    else:
        await websocket.send("user_not_found")
        username = await websocket.recv()
        cursor.execute("INSERT INTO Users (uid, username) VALUES (?, ?)", (uid, username))
        print(f"{username} ({uid}) registered")
        conn.commit()

    user = User(uid, username, websocket)
    connected_users[str(uid)] = user

    unread_messages = await get_unread_messages(uid)
    if unread_messages:
        await websocket.send("您的未讀訊息：")
        for from_uid, message, date in unread_messages:
            from_user = await find_user_by_uid(from_uid)
            await websocket.send(f"[{date}] {from_user.username}: {message}")
    else:
        await websocket.send("目前沒有未讀訊息。")

    return user

async def send_history(user):
    cursor.execute(
        "SELECT from_uid, to_uid, message, date, read FROM Messages WHERE from_uid = ? OR to_uid = ?",
        (user.uid, user.uid)
    )
    history = cursor.fetchall()

    if history:
        await user.websocket.send("歷史訊息紀錄：")
        for from_uid, to_uid, msg, date, read in history:
            from_user = await find_user_by_uid(from_uid)
            to_user = await find_user_by_uid(to_uid)
            await user.websocket.send(f"[{date}] {from_user.username} -> {to_user.username}: {msg} ({'已讀' if read else '未讀'})")
        
        await mark_messages_as_read(user.uid)
    else:
        await user.websocket.send("沒有歷史訊息。")


async def handle_message(user):
    try:
        async for message in user.websocket:
            print(f"Received message from {user.username}: {message}")
            if message == "history":
                print(f"{user.username} requested message history")
                await send_history(user)
            elif '|' in message:
                print(f"{user.username} sent a message")
                target_uid, msg_content = message.split('|', 1)
                target_user = await find_user_by_uid(target_uid)

                if target_user is not None:
                    formatted_message = Message(user.uid, target_user.uid, msg_content)
                    print(formatted_message.format_message())

                    if target_user.websocket:
                        await target_user.websocket.send(formatted_message.format_message())
                    else:
                        print(f"Cannot send message to {target_user.username} ({target_user.uid})")

                    formatted_message.save_to_db()
                    print("message send success")
                else:
                    print("target user not found")
                    await user.websocket.send(f"使用者 UID {target_uid} 不存在")
            elif message == "find":
                print(f"{user.username} requested user list")
                cursor.execute("SELECT * FROM Users")
                users = cursor.fetchall()

                await user.websocket.send("使用者列表：")
                for uid, username in users:
                    await user.websocket.send(f"UID: {uid}, 使用者名稱: {username} {'(上線中)' if connected_users.get(str(uid)) else ''}")
            elif message == "quit":
                break
            else:
                await user.websocket.send("無效指令。")
    except websockets.ConnectionClosed:
        print(f"{user.username} 離線")
        connected_users.pop(user.uid)

async def main():
    async with websockets.serve(main_handler, "0.0.0.0", 12345):
        print("WebSocket 伺服器已啟動，等待連線...")
        await asyncio.Future()  # 保持伺服器運行

async def main_handler(websocket, path):
    user = await register_user(websocket)
    await handle_message(user)

users = []

if __name__ == "__main__":
    asyncio.run(main())