import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Settings: React.FC = () => {
    const navigate = useNavigate(); // 初始化 `useNavigate`，用於頁面導航

    // 初始化已讀訊息狀態，優先從 localStorage 獲取，否則默認為 "已讀"
    const [readReceipt, setReadReceipt] = useState<string>(
        localStorage.getItem('readReceipt') || '已讀'
    );

    // 定義可選的已讀字樣選項
    const options = [
        '已讀',
        '我看過了不過我可能在睡覺或吃飯或打遊戲或發呆或大便或洗澡或不小心按到所以沒辦法馬上回你然後我也有可能會忘記回你但我還是愛你呦啾咪'
    ];

    // 處理儲存按鈕的點擊事件
    const handleSave = () => {
        // 儲存當前選擇的已讀訊息到 localStorage
        localStorage.setItem('readReceipt', readReceipt);
        alert('已儲存'); // 顯示提示訊息
        navigate('/chat'); // 儲存後導向回聊天頁面
    };

    return (
        <div className="p-6">
            {/* 標題 */}
            <h2 className="text-xl font-bold mb-4">設定</h2>

            {/* 已讀訊息選擇區 */}
            <div className="mb-4">
                <label className="block mb-2">選擇已讀字樣：</label>
                <select
                    value={readReceipt} // 綁定狀態
                    onChange={(e) => setReadReceipt(e.target.value)} // 更新狀態
                    className="border p-2 rounded w-full" // 基本樣式，w-full 讓選單填滿容器寬度
                    style={{ whiteSpace: 'pre-wrap' }} // 增加換行支援，適合長文字選項
                >
                    {/* 動態渲染選項 */}
                    {options.map((option, index) => (
                        <option key={index} value={option}>
                            {option}
                        </option>
                    ))}
                </select>
            </div>

            {/* 儲存按鈕 */}
            <button
                onClick={handleSave} // 點擊後執行儲存邏輯
                className="bg-cyan-500 text-white px-4 py-2 rounded hover:bg-cyan-600"
            >
                儲存
            </button>
        </div>
    );
};

export default Settings;
