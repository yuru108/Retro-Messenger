import React, { useContext, useState, useRef, useEffect, useCallback } from 'react';
import { UserContext } from '../../App'; // 引入全域的 UserContext
import UserList from './UserList'; // 用戶列表元件
import ChatArea from './ChatArea'; // 聊天區域元件
import UserProfile from './UserProfile'; // 用戶頭像與登出元件

type ChatRoomProps = {
    socket: WebSocket | null; // 接收 WebSocket 連線
};

// 聊天訊息的類型定義
type ChatMessage = {
    from: string; // 發送訊息者的 username
    content: string; // 訊息內容
    time: string; // 訊息的傳送時間
    read: boolean; // 訊息是否已讀
};

// 用戶資料類型定義
type User = {
    username: string; // 用戶名
    isOnline: boolean; // 是否在線狀態
};

// WebSocket 伺服器 URL
const WS_URL = "ws://127.0.0.1:12345";


const ChatRoom: React.FC <{ socket: WebSocket | null }> = ({ socket }) => {
    // 從 UserContext 取得當前用戶的 username
    const userContext = useContext(UserContext);
    const username = String(userContext?.username) || "testUser123"; // 如果 Context 為空，使用測試用戶

    // 狀態管理
    const [selectedUser, setSelectedUser] = useState<string | null>(null); // 當前選中的聊天對象
    const [messages, setMessages] = useState<{ [key: string]: ChatMessage[] }>({}); // 所有聊天訊息的集合
    const [users, setUsers] = useState<User[]>([
        { username: "Alice", isOnline: true },
        { username: "Bob", isOnline: false },
    ]); // 預設用戶清單

    const ws = useRef<WebSocket | null>(null); // 使用 `useRef` 儲存 WebSocket 連接

    const loadRooms = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/room-list?username=${username}`, {
                credentials: 'include', // 傳遞 Cookie
            });
            if (response.ok) {
                const rooms = await response.json();
                setUsers(rooms.map((room: { room_id: string; room_name: string }) => ({
                    username: room.room_name,
                    isOnline: true // 根據後端邏輯調整在線狀態
                })));
            } else {
                console.error(`Failed to load rooms, status: ${response.status}`);
                const error = await response.json();
                console.error(error);
            }
        } catch (error) {
            console.error("Error fetching room list:", error);
        }
    };
    
    
    useEffect(() => {
        loadRooms();
    }, []);
    

    // 登出處理函數（尚未實作）
    const handleLogout = () => {
        // 可以在這裡處理登出邏輯
    };

    const sendMessage = useCallback(async (message: ChatMessage) => {
        if (selectedUser) {
            const newMessage = {
                from: username,
                content: message.content,
                time: new Date().toLocaleString(), // 本地時間格式化
                read: true,
            };
            setMessages((prev) => ({
                ...prev,
                [selectedUser]: [...(prev[selectedUser] || []), newMessage],
            }));
            
            try {
                await fetch("http://127.0.0.1:12345/send-message", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username,
                        to_room_id: selectedUser,
                        message: message.content
                    })
                });
            } catch (error) {
                console.error("Error sending message:", error);
            }
        }
    }, [selectedUser, username]);
    
    const loadMessageHistory = async (roomId: string) => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/message-history?room_id=${roomId}&username=${username}`);
            if (response.ok) {
                const data = await response.json();
                setMessages((prev) => ({
                    ...prev,
                    [roomId]: data.map((msg: any) => ({
                        from: msg.from_user,
                        content: msg.message,
                        time: new Date(msg.date).toLocaleString(), // 格式化為本地時間
                        read: msg.status
                    }))
                }));
            } else {
                console.error("Failed to load message history");
            }
        } catch (error) {
            console.error("Error fetching message history:", error);
        }
    };
    
    useEffect(() => {
        if (selectedUser) {
            loadMessageHistory(selectedUser);
        }
    }, [selectedUser]);

    const loadUnreadMessages = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/unread-messages?username=${username}`);
            if (response.ok) {
                const unreadMessages = await response.json();
                // 這裡可以更新 UI 來顯示未讀訊息通知
                console.log(unreadMessages);
            }
        } catch (error) {
            console.error("Error fetching unread messages:", error);
        }
    };
    
    useEffect(() => {
        loadUnreadMessages();
    }, []);    
    
    return (
        <div className="flex h-screen">
            {/* 用戶列表區域 */}
            <div className="w-64 min-w-[150px] bg-gray-100 p-4 overflow-y-auto flex flex-col h-full flex-shrink-0">
                <UserList 
                    users={users} 
                    onSelectUser={setSelectedUser}
                    selectedUser={selectedUser} 
                    className="flex-grow"
                />
                <div className="mt-auto">
                    <UserProfile 
                        username={username}
                        onLogout={handleLogout}
                        users={users}
                    />
                </div>
            </div>

            {/* 聊天區域 */}
            <div className="flex-grow flex flex-col">
                {selectedUser && (
                    <ChatArea
                        socket={socket}
                        selectedUser={selectedUser}
                        username={username}
                        messages={messages[selectedUser] || []}
                        onSendMessage={sendMessage}
                    />
                )}
            </div>
        </div>

    );
};

export default ChatRoom;
