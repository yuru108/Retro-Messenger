
import React, { useState } from 'react';
import axios from 'axios';


// 定義 Props 的類型
interface GroupCreationModalProps {
    onClose: () => void; // 關閉模態視窗的回調函數
    onCreate: (group: { groupName: string; members: string[] }) => void; // 創建群組的回調函數
    users: string[]; // 可供選擇的用戶列表
}

// 群組創建模態元件
const GroupCreationModal: React.FC<GroupCreationModalProps> = ({ onClose, onCreate, users }) => {
    // 狀態管理：群組名稱
    const [groupName, setGroupName] = useState<string>('');
    // 狀態管理：已選成員
    const [selectedMembers, setSelectedMembers] = useState<string[]>([]);

    // 處理成員選擇的變更
    const handleMemberChange = (user: string) => {
        setSelectedMembers((prev) =>
            prev.includes(user) // 檢查該用戶是否已選中
                ? prev.filter((member) => member !== user) // 如果已選中，則取消選擇
                : [...prev, user] // 如果未選中，則加入已選成員列表
        );
    };

    // 處理創建群組的邏輯
    const handleCreateGroup = async () => {
        if (groupName && selectedMembers.length > 0) {
            try {
                // 創建群組，發送 POST 請求到後端 Flask API
                const response = await axios.post('http://localhost:12345/create-group', {
                    room_name: groupName,
                    userlist: selectedMembers,
                });
                console.log('Group created:', response.data);
                // 在這裡處理後端的回應，例如可以使用返回的 room_id
                if (response.status === 200) {
                    // 成功創建群組
                    onCreate({ groupName, members: selectedMembers });
                    // 關閉模態視窗
                    onClose();
                } else {
                    // 處理失敗的情況
                    alert('創建群組失敗');
                }
            } catch (error) {
                console.error('創建群組時發生錯誤:', error);
                alert('發生錯誤，請稍後再試');
            }
        }
    };

    return (
        <div className="absolute left-0 bottom-20  bg-white p-4 shadow-lg rounded-lg max-w-md mx-auto z-50">
            {/* 模態標題 */}
            <h2 className="text-lg font-bold mb-4">建立群組</h2>
            
            {/* 群組名稱輸入框 */}
            <input
                type="text"
                placeholder="Group Name"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)} // 更新群組名稱
                className="border rounded w-full px-2 py-1 mb-4"
            />

            {/* 成員選擇列表 */}
            <div>
                <h3 className="font-semibold mb-2">選擇成員</h3>
                {users.map((user) => (
                    <div key={user} className="flex items-center mb-2">
                        {/* 成員選擇複選框 */}
                        <input
                            type="checkbox"
                            checked={selectedMembers.includes(user)} // 檢查該用戶是否已被選中
                            onChange={() => handleMemberChange(user)} // 處理成員選擇變更
                            className="mr-2"
                        />
                        <label className="text-gray-700">{user}</label>
                    </div>
                ))}
            </div>

            {/* 操作按鈕 */}
            <div className="mt-4 flex justify-end space-x-2">
                
                {/* 取消按鈕 */}
                <button
                    onClick={onClose}
                    className="bg-gray-300 text-black px-4 py-2 rounded hover:bg-gray-400"
                >
                    取消
                </button>

                {/* 創建群組按鈕 */}
                <button
                    onClick={handleCreateGroup}
                    className="bg-cyan-500 text-white px-4 py-2 rounded hover:bg-cyan-600"
                    disabled={!groupName || selectedMembers.length === 0} // 禁用條件：群組名稱為空或未選中任何成員
                >
                    確定
                </button>
            </div>
        </div>
    );
};

export default GroupCreationModal;
