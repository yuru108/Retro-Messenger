import { useState, createContext, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import io from 'socket.io-client';
import Login from "./Component/Auth/Login";
import Register from './Component/Auth/Register';
import ChatRoom from './Component/Chat/ChatRoom';
import Settings from './Component/Chat/Settings';

// 創建 UserContext，並設定初始的 username 為 null
export const UserContext = createContext<{ username: string | null }>({ username: null });

const App = () => {
    const [username, setUsername] = useState<string | null>(null);
    const [socket, setSocket] = useState<any>(null); // 更新為 any 類型

    // 建立 Socket.IO 連接
    useEffect(() => {
        const socketInstance = io('http://127.0.0.1:12345', {
            query: { username: username },
            transports: ['websocket', 'polling'],
        });
        
        setSocket(socketInstance);

        return () => {
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
                </Routes>
            </Router>
        </UserContext.Provider>
    );
}

export default App;
