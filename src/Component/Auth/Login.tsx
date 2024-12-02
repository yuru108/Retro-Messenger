import * as React from 'react';
import InputField from './InputField'; // 自訂的輸入框元件
import CustomButton from './CustomButton'; // 自訂的按鈕元件
import { Link, useNavigate } from 'react-router-dom'; // 使用 React Router 的 Link 和 useNavigate
import axios from 'axios'; // 用於 HTTP 請求的庫

// 定義 Login 元件的 props 類型
type LoginProps = {
    onLoginSuccess: (username: string) => void; // 登入成功後的回調函數
};

// Login 元件：處理使用者登入邏輯
const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
    const [username, setUsername] = React.useState(''); // 儲存使用者名稱的狀態
    const [password, setPassword] = React.useState(''); // 儲存密碼的狀態
    const [error, setError] = React.useState<string | null>(null); // 儲存錯誤訊息的狀態
    const navigate = useNavigate(); // 用於導航至其他頁面的鉤子

    // 處理登入按鈕點擊事件
    const handleClick = async () => {
        setError(null); // 清除之前的錯誤訊息
        try {
            // 發送 POST 請求到後端進行登入驗證
            const response = await axios.post('http://localhost:12345/login', { username, password });
    
            // 驗證通過（HTTP 200）時的處理
            if (response.status === 200) {
                console.log('Login successful:', response.data);
    
                // 從回應中提取 username，並將其儲存在 localStorage
                const { username: user } = response.data; // 提取回應中的 username
                localStorage.setItem('username', user); // 儲存 username
    
                // 呼叫父元件傳入的回調函數，將登入資訊傳遞出去
                onLoginSuccess(user);
    
                // 導航到聊天頁面
                navigate('/chat');
            }
        } catch (error: any) {
            // 捕獲錯誤，並設定錯誤訊息
            setError(error.response?.data?.message || 'Login failed. Please try again.');
        }
    };
    

    return (
        <div className="flex flex-col justify-center items-center h-screen">
            {/* 登入頁面的標題 */}
            <h1 className="text-black text-3xl text-center mb-5">Login</h1>

            {/* 如果有錯誤訊息，顯示在此處 */}
            {error && <div className="text-red-500 mb-4">{error}</div>}

            {/* 使用者名稱輸入框 */}
            <InputField 
                label="Username" // 輸入框的標籤
                value={username} // 綁定狀態
                onChange={(e) => setUsername(e.target.value)} // 當值變化時更新狀態
                required // 設為必填
            />

            {/* 密碼輸入框 */}
            <InputField 
                label="Password" // 輸入框的標籤
                type="password" // 設定輸入框類型為密碼
                value={password} // 綁定狀態
                onChange={(e) => setPassword(e.target.value)} // 當值變化時更新狀態
                required // 設為必填
            />

            {/* 登入按鈕 */}
            <CustomButton onClick={handleClick}>Login</CustomButton>

            {/* 註冊連結 */}
            <p className="mt-4">
                <span>沒有帳號嗎？ </span>
                <Link to="/register" className="text-cyan-500 hover:underline">註冊</Link>
            </p>
        </div>
    );
};

export default Login;
