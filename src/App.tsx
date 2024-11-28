import { useState, createContext } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from "./Component/Auth/Login";
import Register from './Component/Auth/Register';
import ChatRoom from './Component/Chat/ChatRoom';
import Settings from './Component/Chat/Settings';
import GroupCreation from './Component/Chat/GroupCreationModal'; // 匯入群組功能元件

// 創建 UserContext，並設定初始的 username 為 null
export const UserContext = createContext<{ username: string | null }>({ username: null });

const App = () => {
    // 設定 username 的 state，初始值為 null
    const [username, setUsername] = useState<string | null>(null);

    return (
        // 將 UserContext 提供給子組件，讓它們能夠讀取 username
        <UserContext.Provider value={{ username }}>
            <Router>
                <Routes>
                    {/* 登入頁面，登入成功後會執行 onLoginSuccess 更新 username */}
                    <Route path="/" element={<Login onLoginSuccess={(userUsername) => setUsername(userUsername)} />} />
                    
                    {/* 註冊頁面 */}
                    <Route path="/register" element={<Register />} />
                    
                    {/* 只有當 username 存在時，才會顯示聊天室頁面 */}
                    {username && <Route path="/chat" element={<ChatRoom />} />}
                    
                    {/* 只有當 username 存在時，才會顯示設定頁面 */}
                    {username && <Route path="/settings" element={<Settings />} />}
                    
                    {/* 群組創建頁面 */}
                    {username && <Route path="/group" element={<GroupCreation onClose={() => {}} onCreate={() => {}} users={[]} />} />}
                </Routes>
            </Router>
        </UserContext.Provider>
    );
}

export default App;
