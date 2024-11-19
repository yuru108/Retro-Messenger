import React, { useContext, useState, useRef, useEffect, useCallback } from 'react';
import { UserContext } from '../../App'; // 引入全域的 UserContext
import UserList from './UserList'; // 用戶列表元件
import ChatArea from './ChatArea'; // 聊天區域元件
import UserProfile from './UserProfile'; // 用戶頭像與登出元件

// 聊天訊息的類型定義
type ChatMessage = {
    from: string; // 發送訊息者的 UID
    content: string; // 訊息內容
    time: string; // 訊息的傳送時間
    read: boolean; // 訊息是否已讀
};

// 用戶資料類型定義
type User = {
    uid: string; // 用戶的唯一識別碼
    username: string; // 用戶名
    isOnline: boolean; // 是否在線狀態
};

// WebSocket 伺服器 URL
const WS_URL = "ws://127.0.0.1:12345";

const ChatRoom: React.FC = () => {
    // 從 UserContext 取得當前用戶的 UID
    const userContext = useContext(UserContext);
    const uid = String(userContext?.uid) || "testUser123"; // 如果 Context 為空，使用測試用戶

    // 狀態管理
    const [selectedUser, setSelectedUser] = useState<string | null>(null); // 當前選中的聊天對象
    const [messages, setMessages] = useState<{ [key: string]: ChatMessage[] }>({}); // 所有聊天訊息的集合
    const [users, setUsers] = useState<User[]>([
        { uid: "user1", username: "Alice", isOnline: true },
        { uid: "user2", username: "Bob", isOnline: false },
    ]); // 預設用戶清單

    const ws = useRef<WebSocket | null>(null); // 使用 `useRef` 儲存 WebSocket 連接

    // 發送訊息的函數
    const sendMessage = useCallback((message: ChatMessage) => {
        if (selectedUser && uid) {
            const { content, time, read } = message;

            // 建立新的訊息物件
            const newMessage: ChatMessage = {
                from: uid,
                content,
                time,
                read,
            };

            // 更新指定用戶的訊息列表
            setMessages((prev) => ({
                ...prev,
                [selectedUser]: [
                    ...(prev[selectedUser] || []), // 確保保留之前的訊息
                    newMessage, // 新增訊息到列表
                ],
            }));

            // 將訊息透過 WebSocket 傳送到伺服器
            if (ws.current) {
                const messageToSend = {
                    to: selectedUser, // 訊息接收者
                    from: uid,        // 訊息發送者
                    content: content, // 訊息內容
                    time: time,       // 發送時間
                };

                // 將訊息轉為 JSON 格式並傳送
                ws.current.send(JSON.stringify(messageToSend));
            }
        }
    }, [selectedUser, uid]);

    // 登出處理函數（尚未實作）
    const handleLogout = () => {
        // 可以在這裡處理登出邏輯
    };

    // 載入訊息歷史紀錄的函數
    const loadMessageHistory = async (selectedUser: string) => {
        const mockData: ChatMessage[] = [
            { from: selectedUser, content: "安安", time: "10:00", read: true },
            { from: uid, content: "在嗎", time: "10:05", read: true },
        ];

        // 將模擬的訊息數據加入到 messages 狀態中
        setMessages((prev) => ({
            ...prev,
            [selectedUser]: mockData,
        }));
    };

    // 當切換選中的聊天對象時載入歷史訊息
    useEffect(() => {
        if (selectedUser) {
            loadMessageHistory(selectedUser);
        }
    }, [selectedUser]);

    return (
        <div className="flex h-screen">
            {/* 用戶列表區域 */}
            <div className="w-64 min-w-[150px] bg-gray-100 p-4 overflow-y-auto flex flex-col h-full">
                {/* 用戶列表 */}
                <UserList 
                    users={users} 
                    onSelectUser={setSelectedUser} // 設定選中的聊天對象
                    selectedUser={selectedUser} // 傳入當前選中的用戶
                    className="flex-grow" // 讓 UserList 占據剩餘空間
                />
                
                {/* 用戶頭像與登出按鈕 */}
                <div className="mt-auto">
                    <UserProfile 
                        uid={uid} // 傳入當前用戶的 UID
                        onLogout={handleLogout} // 傳入登出處理函數
                    />
                </div>
            </div>

            {/* 聊天區域 */}
            <div className="flex-grow flex flex-col">
                {/* 當有選中用戶時顯示聊天區域 */}
                {selectedUser && (
                    <ChatArea
                        selectedUser={selectedUser} // 傳入選中的聊天對象
                        uid={uid} // 傳入當前用戶的 UID
                        messages={messages[selectedUser] || []} // 傳入與該用戶的聊天訊息
                        onSendMessage={sendMessage} // 傳入發送訊息的處理函數
                    />
                )}
            </div>
        </div>
    );
};

export default ChatRoom;
