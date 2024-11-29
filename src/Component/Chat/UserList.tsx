import React from 'react';

// 定義用戶型別
type User = {
    username: string;   // 使用者名稱
    isOnline: boolean;  // 是否在線
};

// 定義元件的屬性型別
type UserListProps = {
    users: User[];                      // 用戶列表
    onSelectUser: (user: string) => void; // 用戶點擊時的回調函數，返回選中的用戶名稱
    selectedUser: string | null;        // 當前選中的用戶名稱
    className?: string;                 // 可選的外部樣式類名，用於自訂樣式
};

const UserList: React.FC<UserListProps> = ({ users, onSelectUser, selectedUser }) => {
    return (
        <div className="space-y-2">
            {/* 如果有用戶，渲染用戶列表，否則顯示提示訊息 */}
            {users.length > 0 ? (
                users.map((user) => (
                    <div
                        key={user.username} // 使用 username 作為唯一的鍵值
                        className={`p-2 cursor-pointer rounded-md shadow-sm 
                            ${user.username === selectedUser ? 'bg-white' : 'bg-slate-50'} 
                            ${user.isOnline ? 'border-l-4 border-green-400' : 'border-l-4 border-red-400'}`}
                        onClick={() => onSelectUser(user.username)} // 點擊時執行回調
                    >
                        {/* 用戶資訊區塊 */}
                        <div className="flex justify-between items-center">
                            {/* 用戶名 */}
                            <span className="font-semibold">{user.username}</span>
                            {/* 在線狀態顯示 */}
                            <span className={`text-sm ${user.isOnline ? 'text-green-600' : 'text-gray-500'}`}>
                                {user.isOnline ? 'Online' : 'Offline'}
                            </span>
                        </div>
                    </div>
                ))
            ) : (
                // 當用戶列表為空時的提示訊息
                <p className="text-center text-gray-500">No users found</p>
            )}
        </div>
    );
};

export default UserList;
