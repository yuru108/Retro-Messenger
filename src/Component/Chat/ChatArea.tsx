import React, { useState, useEffect, useRef } from 'react';
import { Socket } from 'socket.io-client';

// 定義單條訊息的資料結構
type ChatMessage = {
    from: string; // 發送者的 username
    content: string; // 訊息內容
    time: string; // 傳送時間
    read: boolean; // 訊息是否已讀
};

type User = {
    username: string; // 用戶名
    isOnline: boolean; // 是否在線狀態
    roomId: string; // 房間 ID
};

// 定義 ChatArea 元件的屬性類型
type ChatAreaProps = {
    selectedUser: string | null;
    username: string;
    messages: ChatMessage[];
    onSendMessage: (message: ChatMessage) => void;
    socket: typeof Socket | null; // WebSocket 連接
    setUserList: React.Dispatch<React.SetStateAction<User[]>>;
    userList: User[];
    roomId: string; // 新增 roomId
};

// ChatArea 元件
const ChatArea: React.FC<ChatAreaProps> = ({
    selectedUser,
    username,
    messages,
    onSendMessage,
    socket,
    setUserList,
    userList,
    roomId,
}) => {
    const [input, setInput] = useState('');
    const [newRoomName, setNewRoomName] = useState<string>('');
    const [showRoomNameInput, setShowRoomNameInput] = useState<boolean>(false);

    const [readReceipt, setReadReceipt] = useState<string>(
        localStorage.getItem('readReceipt') || '已讀'
    );

    // 訊息列表的參考，用於自動滾動
    const messagesEndRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        // 滾動到訊息底部
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // 傳送訊息
    const sendMessage = () => {
        console.log("selectedUser:", selectedUser);
        console.log("input:", input);
        if (selectedUser && input.trim() !== '' && socket) {
            const time = new Date().toLocaleString();
            const messageData: ChatMessage = {
                from: username,
                content: input,
                time,
                read: false,
            };

            // 將訊息以 JSON 格式傳送到 WebSocket 伺服器
            socket.send(
                JSON.stringify({
                    from_username: username,
                    to_username: selectedUser,
                    message: input,
                })
            );

            // 新增到本地聊天紀錄
            onSendMessage(messageData);
            setInput('');
        }
    };

    // 處理聊天室名稱修改的函數
    const handleRoomNameChange = async () => {
        if (roomId && newRoomName.trim()) {
            console.log("Changing room name...");
            try {
                const response = await fetch('http://127.0.0.1:12345/change-room-name', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        room_id: roomId,
                        room_name: newRoomName,
                    }),
                });
                if (response.ok) {
                    const data = await response.json();
                    console.log("Room ID:", roomId);
                    console.log("New Room Name:", newRoomName);
                    console.log('Room name changed:', data.status);
                } else {
                    const errorData = await response.json();
                    console.error('Failed to change room name:', errorData.error || 'Unknown error');
                }
            } catch (error) {
                console.error('Error changing room name:', error);
            }
        } else {
            console.log('Room ID or new room name is missing');
        }
    };

    return (
        <div className="flex h-screen">
            {/* 聊天區域 */}
            <div className="flex-grow flex flex-col p-4">
                {/* 聊天訊息區 */}
                <div className="flex-1 overflow-y-auto mb-4">
                    <div className="flex justify-between items-center mb-2">
                        <h2 className="text-lg font-semibold">
                            {selectedUser ? `Chat with ${selectedUser}` : 'Select a user to chat'}
                        </h2>

                        {/* 更改房間名稱的按鈕，僅在選擇了用戶後顯示 */}
                        {selectedUser && (
                            <button
                                onClick={() => setShowRoomNameInput(!showRoomNameInput)} // 切換顯示輸入框
                                className="bg-cyan-500 text-white px-4 py-2 rounded-md"
                            >
                                Change Room Name
                            </button>
                        )}
                    </div>

                    {/* 顯示輸入框以更改房間名稱 */}
                    {showRoomNameInput && (
                        <div className="flex mb-4">
                            <input
                                type="text"
                                value={newRoomName}
                                onChange={(e) => setNewRoomName(e.target.value)} // 更新房間名稱
                                placeholder="Enter new room name"
                                className="flex-1 border p-2 rounded-md"
                            />
                            <button
                                onClick={() => {
                                    console.log("Current Room ID:", roomId);
                                    console.log("New Room Name Input:", newRoomName);
                                    handleRoomNameChange();
                                    // 清空輸入框並隱藏輸入區
                                    setNewRoomName('');
                                    setShowRoomNameInput(false);
                                }} // 提交新房間名稱
                                className="bg-cyan-500 text-white px-4 py-2 rounded-md ml-2"
                            >
                                Submit
                            </button>
                        </div>
                    )}

                    <ul>
                        {messages.map((msg, idx) => (
                            <li key={idx} className={`mb-4 flex flex-col ${msg.from === username ? 'items-end' : 'items-start'}`}>
                                {/* 訊息氣泡 */}
                                <div
                                    className={`p-3 rounded-md ${msg.from === username ? 'bg-blue-100' : 'bg-gray-100'}`}
                                    style={{ maxWidth: '66%', wordBreak: 'break-word' }}
                                >
                                    {msg.from === username ? msg.content : `${msg.from}: ${msg.content}`}
                                </div>

                                {/* 顯示訊息時間與是否已讀 */}
                                <span
                                    className="text-gray-400 text-xs mt-1"
                                    style={{
                                        maxWidth: '250px', // 設定最大寬度
                                        whiteSpace: 'normal', // 允許換行
                                    }}
                                >
                                    {msg.time}{' '}
                                    {msg.read ? (
                                        msg.from === username ? (
                                            // 顯示自定義已讀字樣或預設字樣
                                            readReceipt
                                        ) : '已讀'
                                    ) : '未讀'}
                                </span>
                            </li>
                        ))}
                        {/* 放置訊息底部的參考點 */}
                        <div ref={messagesEndRef} />
                    </ul>
                </div>

                {/* 訊息輸入區域，使用 mt-auto 確保其固定在底部 */}
                <div className="flex mt-auto">
                    <input
                        className="flex-1 border p-2 rounded-l-md"
                        value={input}
                        onChange={(e) => setInput(e.target.value)} // 更新輸入框內容
                        placeholder="Type a message"
                    />
                    <button
                        onClick={sendMessage} // 點擊按鈕時傳送訊息
                        className="bg-cyan-500 text-white px-4 py-2 rounded-r-md"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatArea;
