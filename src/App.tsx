import { useState, createContext, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import io from 'socket.io-client';
import Login from "./Component/Auth/Login";
import Register from './Component/Auth/Register';
import ChatRoom from './Component/Chat/ChatRoom';
import Settings from './Component/Chat/Settings';
import GroupCreation from './Component/Chat/GroupCreationModal';

// 創建 UserContext，並設定初始的 username 為 null
export const UserContext = createContext<{ username: string | null }>({ username: null });

const App = () => {
    const [username, setUsername] = useState<string | null>(null);
    const [socket, setSocket] = useState<any>(null); // 更新為 any 類型

    // 建立 Socket.IO 連接
    useEffect(() => {
        const socketInstance = io('http://localhost:12345'); // 使用 io() 建立連接
        setSocket(socketInstance);

        // 當接收到訊息時
        socketInstance.on('message', (messageData: any) => {
            console.log('Received message:', messageData);
        });

        // 當 Socket 斷開時
        socketInstance.on('disconnect', () => {
            console.log('WebSocket connection closed');
        });

        return () => {
            if (socketInstance) socketInstance.disconnect(); // 元件卸載時斷開連接
        };
    }, []);

    return (
        <UserContext.Provider value={{ username }}>
            <Router>
                <Routes>
                    <Route path="/" element={<Login onLoginSuccess={(userUsername) => setUsername(userUsername)} />} />
                    <Route path="/register" element={<Register />} />
                    {/* 傳遞 Socket.IO 連線給 ChatRoom 和 ChatArea */}
                    {username && <Route path="/chat" element={<ChatRoom socket={socket} />} />}
                    {username && <Route path="/settings" element={<Settings />} />}
                    {username && <Route path="/group" element={<GroupCreation onClose={() => {}} onCreate={() => {}} users={[]} />} />}
                </Routes>
            </Router>
        </UserContext.Provider>
    );
}

export default App;
