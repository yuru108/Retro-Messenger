import asyncio
import websockets
from asyncio import Queue

message_queue = Queue()

async def connect_to_server():
    """連接伺服器"""
    uri = "ws://127.0.0.1:12345"
    try:
        async with websockets.connect(uri) as websocket:
            print("成功連接至伺服器！")

            # 啟動接收訊息的非同步任務
            asyncio.create_task(receive_messages(websocket))
    
            # await main_menu(websocket)
    except Exception as e:
        print(f"無法連接伺服器：{e}")

async def receive_messages(websocket):
    """非同步接收伺服器訊息，並將其放入佇列"""
    while True:
        try:
            message = await websocket.recv()
            await message_queue.put(message)
        except websockets.ConnectionClosed:
            print("伺服器已斷開連接")
            break

async def register(websocket, username, password):
    """註冊新使用者"""
    await websocket.send("register")
    await websocket.send(username)
    await websocket.send(password)

    response = await message_queue.get()
    if response == "user_already_exists":
        print(f"使用者 {username} 已存在")
        return {"message": "User already exists"}
    else:
        uid = response
        print(f"註冊成功：{username} ({uid})")
        return {'message': 'Registration successful', 'uid': uid, 'username': username}

async def login(websocket, uid, password):
    """使用 UID 登入"""
    await websocket.send("login")
    await websocket.send(uid)
    await websocket.send(password)

    response = await message_queue.get()
    if response == "login_error":
        print(f"登入失敗")
        return {'message': 'login_error', 'uid': {uid}}
    else:
        print(f"登入成功：{response} ({uid})")
        return {'message': 'Login successful', 'uid': {uid}, 'username': {response}}

async def get_user_list(websocket):
    """獲取使用者清單"""
    await websocket.send("get_user_list")
    response = await message_queue.get()

    users = []
    print("\n使用者清單：")
    for user in response.split("\n"):
        print(user)

        parts = user.split(" ")
        uid = parts[0]
        username = parts[1]
        isOnline = True if parts[-1] == "isOnline" else False
        users.append({'uid': uid, 'username': username, 'isOnline': isOnline})

    return users

async def get_room_list(websocket):
    """獲取房間清單"""
    await websocket.send("get_room_list")
    response = await message_queue.get()

    rooms = []
    print("\n房間清單：")
    for room in response.split("\n"):
        print(room)

        parts = room.split(" ")
        room_id = parts[0]
        room_name = parts[1]
        rooms.append({'room_id': room_id, 'room_name': room_name})

    return rooms

async def send_message(websocket, from_uid, to_room_id, message):
    """傳送訊息"""
    await websocket.send(f"send_message {from_uid} {to_room_id} {message}")
    response = await message_queue.get()
    print(response)

    if response == "訊息已發送":
        return True
    else:
        return False

async def get_message_history(websocket, room_id):
    """獲取該 room_id 的訊息歷史紀錄"""
    await websocket.send(f"get_messages_history {room_id}")
    response = await message_queue.get()

    messages = []
    print("\n歷史訊息：")
    for message in response.split("\n"):
        print(message)

        parts = message.split(" ")
        room_name = parts[0]
        from_user = parts[1]
        msg = parts[2]
        date = parts[3]
        status = True if parts[4] == "已讀" else False
        messages.append({'room_name': room_name, 'from_user': from_user, 'message': msg, 'date': date, 'status': status})

    return messages

async def get_unread_messages(websocket, uid):
    """獲取所有未讀訊息"""
    await websocket.send(f"get_unread_messages {uid}")
    response = await message_queue.get()

    messages = []
    print("\n未讀訊息：")
    for message in response.split("\n"):
        print(message)

        parts = message.split(" ")
        room_name = parts[0]
        from_user = parts[1]
        msg = parts[2]
        date = parts[3]
        status = True if parts[4] == "已讀" else False
        messages.append({'room_name': room_name, 'from_user': from_user, 'message': msg, 'date': date, 'status': status})

    return messages

# async def main_menu(websocket):
#     """客戶端主功能菜單"""
#     print("選擇操作：1) 註冊 2) 登入")
#     action = input("請輸入操作：").strip()

#     if action == "1":
#         await register(websocket, "user2")
#     elif action == "2":
#         login_success = await login(websocket, "2")
#         if login_success:
#             await logged_in_menu(websocket)
#     else:
#         print("無效操作，請重新選擇。")

# async def logged_in_menu(websocket):
#     """登入後的功能菜單"""
#     while True:
#         print("\n選擇操作：")
#         print("1) 查看使用者清單")
#         print("2) 查詢房間訊息")
#         print("3) 傳送訊息至房間")
#         print("4) 查看房間清單")
#         print("5) 所有未讀訊息")
#         print("5) 退出")
#         action = input("請輸入操作：").strip()

#         if action == "1":
#             await get_user_list(websocket)
#         elif action == "2":
#             room_id = input("請輸入房間 ID：").strip()
#             await get_message_history(websocket, room_id)
#         elif action == "3":
#             room_id = input("請輸入房間 ID：").strip()
#             await send_message(websocket, "1", room_id, "Hello, world!")
#         elif action == "4":
#             await get_room_list(websocket)
#         elif action == "5":
#             await get_unread_messages(websocket, "2")
#         elif action == "6":
#             print("已退出客戶端。")
#             break
#         else:
#             print("無效操作，請重新選擇。")

asyncio.run(connect_to_server())