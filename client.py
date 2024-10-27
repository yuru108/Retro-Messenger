import asyncio
import websockets

async def connect_to_server():
    uri = "ws://127.0.0.1:12345"
    async with websockets.connect(uri) as websocket:
        username_prompt = await websocket.recv()
        print(username_prompt)
        uid = input("輸入uid: ")
        await websocket.send(uid)

        username = await websocket.recv()
        if username == "user_not_found":
            username = input("輸入使用者名稱: ")
            await websocket.send(username)
        else:
            print(f"歡迎回來，{username}！")

        # 啟動接收訊息的非同步任務
        asyncio.create_task(receive_messages(websocket))

        # 傳送指令的主迴圈
        await send_action(websocket)

async def receive_messages(websocket):
    """非同步接收伺服器訊息，並即時顯示"""
    while True:
        try:
            message = await websocket.recv()
            print(f"\n{message}")
        except websockets.ConnectionClosed:
            print("伺服器已斷開連接")
            break

async def send_action(websocket):
    """非同步傳送使用者指令"""
    while True:
        # 使用 await 等待 to_thread 的執行結果
        action = await asyncio.to_thread(input, "\n選擇動作 (new: 傳送新訊息, history: 查看歷史紀錄, find: 查看使用者列表, quit: 離開): ")
        action = action.lower()

        if action == "quit":
            print("正在離開...")
            await websocket.send(action)
            break
        elif action == "history":
            await websocket.send("history")
        elif action == "new":
            target_uid = input("輸入目標 UID: ")
            message = input("輸入訊息: ")
            await websocket.send(f"{target_uid}|{message}")
        elif action == "find":
            await websocket.send("find")
        else:
            print("無效指令，請再試一次。")

# 啟動客戶端
asyncio.run(connect_to_server())