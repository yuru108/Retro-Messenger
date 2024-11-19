import * as React from 'react';
import InputField from './InputField'; // 引入自訂的輸入框元件
import CustomButton from './CustomButton'; // 引入自訂的按鈕元件
import { Link, useNavigate } from 'react-router-dom'; // 引入 react-router-dom 中的 Link 和 useNavigate
import axios from 'axios'; // 引入 Axios，用於發送 HTTP 請求

// 註冊頁面元件
const Register = () => {
    // 定義狀態變數
    const [username, setUsername] = React.useState(''); // 儲存使用者輸入的使用者名稱
    const [password, setPassword] = React.useState(''); // 儲存使用者輸入的密碼
    const [error, setError] = React.useState<string | null>(null); // 用來顯示錯誤訊息
    const [successMessage, setSuccessMessage] = React.useState<string | null>(null); // 用來顯示註冊成功的訊息
    const navigate = useNavigate(); // 使用 useNavigate 進行頁面導航

    // 處理註冊邏輯
    const handleRegister = async () => {
        try {
            // 發送 POST 請求，將 username 和 password 傳送到後端 API
            const response = await axios.post('http://localhost:12345/register', { username, password });

            // 假設後端返回 201 狀態碼表示成功
            if (response.status === 201) {
                console.log('Registration successful:', response.data);

                // 顯示成功訊息
                setSuccessMessage('註冊成功，請登入！');
                setError(null); // 清空錯誤訊息

                // 2 秒後自動導航到登入頁面
                setTimeout(() => {
                    navigate('/'); // 導航到根路徑（登入頁面）
                }, 2000);
            } else {
                // 如果不是 201 狀態碼，顯示後端返回的錯誤訊息
                setError(response.data.message || '註冊失敗，請再試一次。');
            }
        } catch (error: any) {
            // 處理 HTTP 請求錯誤，顯示後端返回的錯誤訊息或預設訊息
            setError(error.response?.data?.message || '註冊失敗，請再試一次。');
        }
    };

    return (
        <div className="flex flex-col justify-center items-center h-screen">
            {/* 註冊頁面標題 */}
            <h1 className="text-black text-3xl text-center mb-5">Register</h1>

            {/* 顯示錯誤訊息 */}
            {error && <div className="text-red-500 mb-4">{error}</div>}

            {/* 顯示成功訊息 */}
            {successMessage && <div className="text-green-500 mb-4">{successMessage}</div>}

            {/* 使用自訂的 InputField 元件來輸入使用者名稱 */}
            <InputField
                label="Username" // 標籤文字
                value={username} // 綁定使用者名稱的狀態
                onChange={(e) => setUsername(e.target.value)} // 更新狀態的處理函數
                required // 表示此欄位為必填
            />

            {/* 使用自訂的 InputField 元件來輸入密碼 */}
            <InputField
                label="Password" // 標籤文字
                type="password" // 設定輸入框類型為密碼
                value={password} // 綁定密碼的狀態
                onChange={(e) => setPassword(e.target.value)} // 更新狀態的處理函數
                required // 表示此欄位為必填
            />

            {/* 註冊按鈕 */}
            <CustomButton onClick={handleRegister}>Register</CustomButton>

            {/* 提供登入頁面的連結 */}
            <p className="mt-4">
                <span>已經有帳號嗎？ </span>
                {/* 使用 Link 元件來導航到登入頁面 */}
                <Link to="/" className="text-cyan-500 hover:underline">登入</Link>
            </p>
        </div>
    );
};

export default Register;
