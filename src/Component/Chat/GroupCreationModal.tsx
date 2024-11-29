import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface GroupCreationModalProps {
    onClose: () => void;
    onCreate: (group: { groupName: string; members: string[] }) => void;
}

const GroupCreationModal: React.FC<GroupCreationModalProps> = ({ onClose, onCreate }) => {
    const [groupName, setGroupName] = useState<string>('');
    const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
    const [users, setUsers] = useState<string[]>([]); // 用戶列表

    // 獲取用戶列表
    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:12345/user-list');
                const usersData = response.data;
                
                if (Array.isArray(usersData)) {
                    setUsers(usersData.map((user: { username: string }) => user.username));
                } else {
                    console.error("Invalid response format:", usersData);
                    setUsers([]);
                }
            } catch (error) {
                console.error("Axios error:", error);
                setUsers([]); // 在錯誤情況下設置為空陣列，避免 map 錯誤
            }
        };
        
        fetchUsers();
    }, []);
    

    const handleMemberChange = (user: string) => {
        setSelectedMembers((prev) =>
            prev.includes(user) ? prev.filter((member) => member !== user) : [...prev, user]
        );
    };

    const handleCreateGroup = async () => {
        if (groupName && selectedMembers.length > 0) {
            try {
                const response = await axios.post('http://127.0.0.1:12345/create-room', {
                    room_name: groupName,
                    userlist: selectedMembers,
                });

                if (response.status === 200) {
                    onCreate({ groupName, members: selectedMembers });
                    onClose();
                } else {
                    alert('創建群組失敗');
                }
            } catch (error) {
                console.error('創建群組時發生錯誤:', error);
                alert('發生錯誤，請稍後再試');
            }
        }
    };

    return (
        <div className="absolute left-0 bottom-20 bg-white p-4 shadow-lg rounded-lg max-w-md mx-auto z-50">
            <h2 className="text-lg font-bold mb-4">建立群組</h2>
            <input
                type="text"
                placeholder="Group Name"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="border rounded w-full px-2 py-1 mb-4"
            />
            <div>
                <h3 className="font-semibold mb-2">選擇成員</h3>
                {users.map((user) => (
                    <div key={user} className="flex items-center mb-2">
                        <input
                            type="checkbox"
                            checked={selectedMembers.includes(user)}
                            onChange={() => handleMemberChange(user)}
                            className="mr-2"
                        />
                        <label className="text-gray-700">{user}</label>
                    </div>
                ))}
            </div>
            <div className="mt-4 flex justify-end space-x-2">
                <button onClick={onClose} className="bg-gray-300 text-black px-4 py-2 rounded hover:bg-gray-400">
                    取消
                </button>
                <button
                    onClick={handleCreateGroup}
                    className="bg-cyan-500 text-white px-4 py-2 rounded hover:bg-cyan-600"
                    disabled={!groupName || selectedMembers.length === 0}
                >
                    確定
                </button>
            </div>
        </div>
    );
};

export default GroupCreationModal;
