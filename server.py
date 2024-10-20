import socket
import threading
from datetime import datetime

HOST = '0.0.0.0'
PORT = 12345

class User:
    def __init__(self, uid, addr, username, conn):
        self.uid = uid
        self.addr = addr
        self.username = username
        self.conn = conn

class Message:
    def __init__(self, from_uid, to_uid, message):
        self.from_uid = from_uid
        self.to_uid = to_uid
        self.message = message
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def format_message(self):
        return f"[{self.date}] User {self.from_uid} -> User {self.to_uid}: {self.message}"

users = []
uid_counter = 1

def find_user_by_uid(uid):
    """根據 UID 查找使用者"""
    for user in users:
        if user.uid == int(uid):
            return user
    return None

def handle_user(user):
    """處理每個使用者的訊息"""
    while True:
        try:
            # 接收來自 client 的資料 (格式: 目標 UID|訊息內容)
            data = user.conn.recv(1024).decode('utf-8')
            if data:
                target_uid, msg_content = data.split('|', 1)
                target_user = find_user_by_uid(target_uid)

                if target_user:
                    message = Message(user.uid, target_user.uid, msg_content)
                    print(message.format_message())
                    target_user.conn.send(message.format_message().encode('utf-8'))
                else:
                    user.conn.send(f"使用者 UID {target_uid} 不存在".encode('utf-8'))
            else:
                raise Exception("連線中斷")
        except:
            print(f"{user.username} 離線")
            users.remove(user)
            user.conn.close()
            broadcast(f"{user.username} 已離開聊天室".encode('utf-8'))
            break

def broadcast(message):
    """廣播訊息給所有使用者"""
    for user in users:
        try:
            user.conn.send(message)
        except:
            users.remove(user)

def main():
    global uid_counter
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"伺服器啟動，等待連線中... ({HOST}:{PORT})")

    while True:
        conn, addr = server.accept()
        conn.send("請輸入使用者名稱: ".encode('utf-8'))
        username = conn.recv(1024).decode('utf-8')

        user = User(uid_counter, addr, username, conn)
        uid_counter += 1

        users.append(user)
        print(f"{username} (UID: {user.uid}) 來自 {addr} 已加入聊天室")
        broadcast(f"{username} 已加入聊天室 (UID: {user.uid})".encode('utf-8'))

        threading.Thread(target=handle_user, args=(user,)).start()

if __name__ == "__main__":
    main()