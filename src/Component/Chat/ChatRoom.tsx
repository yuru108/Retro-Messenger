import React, { useContext, useState, useEffect, useCallback } from 'react';
import { UserContext } from '../../App'; // 引入全域的 UserContext
import UserList from './UserList'; // 用戶列表元件
import ChatArea from './ChatArea'; // 聊天區域元件
import UserProfile from './UserProfile'; // 用戶頭像與登出元件
import io from 'socket.io-client'; // 引入 socket.io-client

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
    roomId: string; // 房間 ID
};

const socket = io("http://localhost:12345");

const ChatRoom: React.FC<{ socket: WebSocket | null }> = ({ socket }) => {
    const userContext = useContext(UserContext);
    const username = String(userContext?.username) || "testUser123"; // 如果 Context 為空，使用測試用戶

    // 狀態管理
    const [selectedUser, setSelectedUser] = useState<string | null>(null); // 當前選中的聊天對象
    const [messages, setMessages] = useState<{ [key: string]: ChatMessage[] }>({}); // 所有聊天訊息的集合
    const [users, setUsers] = useState<User[]>([]); // 用戶清單
    const [roomId, setRoomId] = useState<string>(''); // 當前房間 ID

    const loadRooms = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/room-list?username=${username}`);
            if (response.ok) {
                const rooms = await response.json();
                setUsers(rooms.map((room: { room_id: string; room_name: string; isOnline: boolean }) => ({
                    username: room.room_name,
                    isOnline: room.isOnline,
                    roomId: room.room_id,
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

        socket.on('room_list_update', (updatedRoomList) => {
            console.log("Received updated room list:", updatedRoomList);
            setUsers(updatedRoomList);
        });

        return () => {
            socket.off('room_list_update');
        };
    }, []);

    // 當選擇用戶時，設置對應的 roomId
    const handleSelectUser = (username: string) => {
        
        setSelectedUser(username);  // 設置 selectedUser 為選中的 username
        // 根據選中的 username 設置對應的 roomId
        const selectedRoom = users.find(user => user.username === username);
        if (selectedRoom) {
            setRoomId(selectedRoom.roomId);  // 使用該 username 的 roomId
        }
    };      

    const sendMessage = useCallback(async (message: ChatMessage) => {
        console.log("selectedUser:", selectedUser);
        console.log("roomId:", roomId); // 確保 roomId 已經正確設置
    
        if (roomId) { // 這裡檢查 roomId 是否存在
            const newMessage = {
                from: username,
                content: message.content,
                time: new Date().toLocaleString(),
                read: false,
            };
            
            // 更新訊息狀態，顯示發送的訊息
            setMessages((prev) => {
                const updatedMessages = {
                    ...prev,
                    [roomId]: [...(prev[roomId] || []), newMessage], // 根據 roomId 更新訊息
                };
                console.log("Updated messages:", updatedMessages); // 檢查更新後的 messages
                return updatedMessages;
            });
    
            try {
                const response = await fetch("http://127.0.0.1:12345/send-message", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        username,
                        to_room_id: roomId, // 使用正確的 roomId
                        message: message.content,
                    }),
                });
    
                console.log({
                    username,
                    to_room_id: roomId,
                    message: message.content
                });
    
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to send message');
                }
            } catch (error) {
                console.error("Error sending message:", error);
            }
        }
    }, [selectedUser, roomId, username]);
    

    const loadMessageHistory = async (roomId: string, username: string) => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/message-history?room_id=${roomId}&username=${username}`);
            if (response.ok) {
                const data = await response.json();
                if (data.message === "no_messages") {
                    console.log("No messages found for this room.");
                    setMessages((prev) => ({
                        ...prev,
                        [roomId]: [] // 設置為空陣列表示沒有訊息
                    }));
                } else if (Array.isArray(data)) {
                    setMessages((prev) => ({
                        ...prev,
                        [roomId]: data.map((msg: any) => ({
                            from: msg.from_user,
                            content: msg.message,
                            time: new Date(msg.date).toLocaleString(),
                            read: msg.status
                        }))
                    }));
                } else {
                    console.error("Unexpected data format:", data);
                }
            } else {
                console.error("Failed to load message history");
            }
        } catch (error) {
            console.error("Error fetching message history:", error);
        }
    };

    useEffect(() => {
        if (roomId && username) {
            loadMessageHistory(roomId, username);
        } else {
            console.warn("Missing room ID or username here.");
        }

        socket.on('history_update', (message) => {
            console.log("Received message:", message);
            setMessages((prev) => {
                const updatedMessages = {
                    ...prev,
                    [message.room_id]: [...(prev[message.room_id] || []), {
                        from: message.from_user,
                        content: message.message,
                        time: new Date(message.date).toLocaleString(),
                        read: message.status
                    }]
                };
                console.log("Updated messages:", updatedMessages);
                return updatedMessages;
            });
        });

        return () => {
            socket.off('history_update');
        };
    }, [roomId, username]);

    const loadUnreadMessages = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:12345/unread-messages?username=${username}`);
            if (response.ok) {
                const unreadMessages = await response.json();
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
                    onSelectUser={handleSelectUser} // 用戶選擇後更新 selectedUser 和 roomId
                    selectedUser={selectedUser} 
                    className="flex-grow"
                />
                <div className="mt-auto">
                    <UserProfile 
                        username={username}
                        onLogout={() => {}} // 登出處理函數
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
                        messages={messages[roomId] || []} // 使用 roomId 來獲取正確的訊息
                        onSendMessage={sendMessage}
                    />
                )}
            </div>
        </div>
    );
};

export default ChatRoom;
