import React, { useState, useRef, useEffect } from 'react';
import Modal from './Modal'; // 匯入彈窗元件
import { useNavigate } from 'react-router-dom';
import GroupCreationModal from './GroupCreationModal'; // 匯入群組創建模態元件

type UserProfileProps = {
    uid: string;            // 使用者的 UID
    onLogout: () => void;   // 登出的回調函數
    users: { username: string }[]; // 新增 users 資料型別
};

const UserProfile: React.FC<UserProfileProps> = ({ uid, onLogout, users }) => {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false); // 控制下拉選單是否開啟
    const [isModalOpen, setIsModalOpen] = useState(false);       // 控制登出彈窗是否開啟
    const [isGroupModalOpen, setIsGroupModalOpen] = useState(false); // 控制群組創建彈窗是否開啟
    const [username, setUsername] = useState<string | null>(null); // 儲存使用者名稱
    const dropdownRef = useRef<HTMLDivElement | null>(null);     // 下拉選單的參考
    const buttonRef = useRef<HTMLDivElement | null>(null);       // 點擊按鈕的參考
    const navigate = useNavigate(); // 用於頁面導航

    // 從 localStorage 取得使用者名稱
    useEffect(() => {
        const storedUsername = localStorage.getItem('username');
        if (storedUsername) {
            setUsername(storedUsername);
        }
    }, []);

    // 監聽點擊事件，檢測是否點擊在下拉選單外部
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
                buttonRef.current && !buttonRef.current.contains(event.target as Node)
            ) {
                setIsDropdownOpen(false); // 點擊外部關閉下拉選單
            }
        };

        document.addEventListener('click', handleClickOutside); // 註冊點擊事件
        return () => {
            document.removeEventListener('click', handleClickOutside); // 清除事件
        };
    }, []);

    // 切換下拉選單開關
    const toggleDropdown = () => {
        setIsDropdownOpen(prev => !prev);
    };

    // 處理登出按鈕的點擊
    const handleLogout = () => {
        setIsModalOpen(true); // 打開登出彈窗
    };

    // 確認登出
    const confirmLogout = () => {
        onLogout();        // 呼叫父層傳入的登出邏輯
        setIsModalOpen(false);
        navigate('/');     // 導航至登入頁面
    };

    // 取消登出
    const cancelLogout = () => {
        setIsModalOpen(false); // 關閉彈窗
    };

    // 處理點擊設定選項
    const handleSettings = () => {
        setIsDropdownOpen(false); // 關閉下拉選單
        navigate('/settings');    // 導航到設定頁面
    };

    // 處理點擊建群組選項
    const handleCreateGroup = () => {
        setIsDropdownOpen(false); // 關閉下拉選單
        setIsGroupModalOpen(true); // 顯示群組創建模態框
    };

    // 處理創建群組
    const handleCreateGroupCallback = (group: { groupName: string; members: string[] }) => {
        console.log('Group Created:', group); // 在控制台顯示群組名稱與成員
        setIsGroupModalOpen(false); // 關閉群組創建模態框
    };

    return (
        <div className="relative flex items-center justify-between">
            {/* 使用者資訊與頭像 */}
            <div className="flex items-center cursor-pointer" ref={buttonRef} onClick={toggleDropdown}>
                {/* 頭像 */}
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">{uid[0]}</span> {/* 顯示 UID 的第一個字元 */}
                </div>

                {/* 使用者名稱與 UID */}
                <div className="ml-4">
                    <div className="text-gray-800 font-medium">
                        {username || 'No Username'} {/* 預設顯示 "No Username" */}
                    </div>
                    <div className="text-gray-500 text-sm">
                        {uid}
                    </div>
                </div>
            </div>

            {/* 下拉選單 */}
            {isDropdownOpen && (
                <div
                    ref={dropdownRef}
                    className="absolute left-0 bottom-20 w-30 bg-white shadow-md rounded-md border z-20"
                >
                    <button
                        className="w-full text-left py-2 px-4 text-gray-700 hover:bg-gray-100"
                        onClick={handleCreateGroup} // 點擊開啟群組創建頁面
                    >
                        建群組
                    </button>
                    <button
                        className="w-full text-left py-2 px-4 text-gray-700 hover:bg-gray-100"
                        onClick={handleSettings} // 點擊導向設定頁面
                    >
                        設定
                    </button>
                    <button
                        className="w-full text-left py-2 px-4 text-red-400 hover:bg-gray-100"
                        onClick={handleLogout} // 點擊開啟登出彈窗
                    >
                        登出
                    </button>
                </div>
            )}

            {/* 彈窗確認登出 */}
            <Modal
                isOpen={isModalOpen}
                onClose={cancelLogout}    // 關閉彈窗
                onConfirm={confirmLogout} // 確認登出
                message="確定要登出嗎？"   // 彈窗顯示訊息
            />

            {/* 顯示群組創建模態框 */}
            {isGroupModalOpen && (
                <GroupCreationModal
                    onClose={() => setIsGroupModalOpen(false)} // 關閉群組創建模態框
                    onCreate={handleCreateGroupCallback} // 創建群組回調
                    users={users.map(user => user.username)} // 傳遞用戶名稱列表
                />
            )}
        </div>
    );
};

export default UserProfile;
