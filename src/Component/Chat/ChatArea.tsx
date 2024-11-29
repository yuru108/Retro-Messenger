import React, { useState, useEffect } from 'react';

// 定義單條訊息的資料結構
type ChatMessage = {
    from: string; // 發送者的 username
    content: string; // 訊息內容
    time: string; // 傳送時間
    read: boolean; // 訊息是否已讀
};

// 定義 ChatArea 元件的屬性類型
type ChatAreaProps = {
    selectedUser: string | null; // 被選中的聊天對象 username
    username: string; // 當前使用者的 username
    messages: ChatMessage[]; // 傳入的訊息陣列
    onSendMessage: (message: ChatMessage) => void; // 傳送訊息的回呼函數
};

// ChatArea 元件
const ChatArea: React.FC<ChatAreaProps> = ({ selectedUser, username, messages, onSendMessage }) => {
    const [input, setInput] = useState(''); // 用於儲存訊息輸入框的內容
    const [socket, setSocket] = useState<WebSocket | null>(null); // 用於儲存 WebSocket 連接

    // 儲存用戶是否自定義 "已讀" 字樣，從 localStorage 獲取
    const [readReceipt, setReadReceipt] = useState<string>(
        localStorage.getItem('readReceipt') || '已讀'
    );

    // 建立與 WebSocket 伺服器的連接
    useEffect(() => {
        if (socket) return; // 如果已有連接，則不重複建立

        const ws = new WebSocket('ws://localhost:12345'); // 初始化 WebSocket，連接本地伺服器
        setSocket(ws); // 設定 WebSocket 實例

        // 當接收到伺服器的訊息時觸發
        ws.onmessage = (event) => {
            const messageData = JSON.parse(event.data); // 將訊息 JSON 轉為物件
            const { from_username, message } = messageData; // 解構訊息內容

            // 如果訊息來自當前選中的聊天對象，則新增到聊天紀錄中
            if (from_username === selectedUser) {
                const time = new Date().toLocaleTimeString(); // 訊息傳送時間
                onSendMessage({ from: from_username, content: message, time, read: false });
            }
        };

        // 當元件卸載時關閉 WebSocket 連接
        return () => {
            if (ws) ws.close();
        };
    }, [selectedUser, socket, onSendMessage]);

    // 傳送訊息
    const sendMessage = () => {
        if (selectedUser && input.trim() !== '' && socket) {
            const time = new Date().toLocaleString(); // 使用本地時間
            const messageData: ChatMessage = {
                from: username, // 發送者是當前使用者
                content: input, // 傳送的訊息內容
                time, // 傳送時間
                read: false, // 預設為未讀
            };

            // 將訊息以 JSON 格式傳送到 WebSocket 伺服器
            socket.send(JSON.stringify({
                from_username: username,
                to_username: selectedUser,
                message: input,
            }));

            // 新增到本地聊天紀錄
            onSendMessage(messageData);
            setInput(''); // 清空輸入框
        }
    };

    return (
        <div className="flex-1 flex flex-col p-4">
            {/* 聊天訊息區 */}
            <div className="flex-1 overflow-y-auto mb-4">
                <h2 className="text-lg font-semibold">
                    {selectedUser ? `Chat with ${selectedUser}` : 'Select a user to chat'}
                </h2>
                <ul>
                    {messages.map((msg, idx) => (
                        <li key={idx} className={`mb-4 flex flex-col ${msg.from === username ? 'items-end' : 'items-start'}`}>
                            {/* 訊息氣泡 */}
                            <div
                                className={`p-3 rounded-md ${msg.from === username ? 'bg-blue-100' : 'bg-gray-100'}`}
                                style={{ maxWidth: '66%', wordBreak: 'break-word' }}
                            >
                                {/* 如果是自己傳送的訊息，只顯示內容；否則顯示發送者 username */}
                                {msg.from === username ? msg.content : `${msg.from}: ${msg.content}`}
                            </div>

                            {/* 顯示訊息時間與是否已讀 */}
                            <span
                                className="text-gray-400 text-xs mt-1"
                                style={{
                                    maxWidth: '50%', // 限制寬度
                                    whiteSpace: 'normal', // 自動換行
                                    wordBreak: 'break-word', // 強制換行
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
                </ul>
            </div>

            {/* 訊息輸入區域 */}
            <div className="flex">
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
    );
};

export default ChatArea;
