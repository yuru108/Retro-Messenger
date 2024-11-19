import React from 'react';

// 定義 ModalProps 的類型
type ModalProps = {
    isOpen: boolean; // 控制模態是否開啟
    onClose: () => void; // 關閉模態的回調函數
    onConfirm: () => void; // 確認操作的回調函數
    message: string; // 彈窗顯示的訊息
};

// 定義 Modal 組件
const Modal: React.FC<ModalProps> = ({ isOpen, onClose, onConfirm, message }) => {
    // 如果模態未開啟，返回 null，不渲染任何內容
    if (!isOpen) return null;

    return (
        <div 
            className="fixed inset-0 bg-gray-500 bg-opacity-50 flex justify-center items-center z-50"
            aria-hidden={!isOpen} // ARIA 屬性，提示模態是否隱藏
        >
            {/* 模態的內容區塊 */}
            <div className="bg-white rounded-lg shadow-lg p-6 max-w-sm w-full">
                {/* 顯示訊息 */}
                <h2 className="text-xl font-semibold text-gray-800 mb-4">{message}</h2>

                {/* 操作按鈕區域 */}
                <div className="flex justify-end space-x-4">
                    {/* 取消按鈕 */}
                    <button
                        className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400"
                        onClick={onClose} // 點擊後執行 onClose 函數
                    >
                        取消
                    </button>

                    {/* 確認按鈕 */}
                    <button
                        className="px-4 py-2 bg-cyan-500 text-white rounded-md hover:bg-cyan-600"
                        onClick={onConfirm} // 點擊後執行 onConfirm 函數
                    >
                        確認登出
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Modal;
