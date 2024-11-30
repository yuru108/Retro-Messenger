import * as React from 'react';
import { FormControl, useFormControlContext } from '@mui/base/FormControl';
import { Input } from '@mui/base/Input';
import clsx from 'clsx';

// 定義 InputField 的屬性類型
interface InputFieldProps {
    label: string; // 標籤文字，例如 "Username"
    type?: string; // 輸入框的類型，例如 "password" 或 "text"，預設為 "text"
    value: string; // 輸入框的值
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; // 值改變時的回呼函式
    required?: boolean; // 是否為必填欄位，預設為非必填
}

// Label 元件：顯示輸入框上方的標籤文字，並自動判斷是否需要顯示「必填 *」
const Label = React.forwardRef<
    HTMLParagraphElement,
    { className?: string; children?: React.ReactNode }
>(({ className: classNameProp, children }, ref) => {
    
    // 使用 MUI 提供的 useFormControlContext 取得上下文
    const formControlContext = useFormControlContext();
    const [dirty, setDirty] = React.useState(false); // 用於判斷輸入框是否被修改過

    // 當輸入框已被填寫時，設定 dirty 狀態為 true
    React.useEffect(() => {
        if (formControlContext?.filled) {
            setDirty(true);
        }
    }, [formControlContext]);

    console.log(dirty);

    // 如果沒有上下文，直接渲染標籤文字（不顯示 *）
    if (formControlContext === undefined) {
        return <p className={clsx('text-sm mb-1', classNameProp)}>{children}</p>;
    }

    const { required } = formControlContext; // 從上下文中取得是否為必填

    return (
        <p
            ref={ref}
            className={clsx(
                'text-sm mb-1', // 標籤文字的基本樣式
                classNameProp // 允許外部傳入額外的樣式
            )}
        >
            {children}
            {required ? ' *' : ''} {/* 如果為必填，顯示星號 */}
        </p>
    );
});

// HelperText 元件：輸入框下方的輔助文字，用於顯示錯誤提示
const HelperText = React.forwardRef<HTMLParagraphElement, { className?: string }>(
    (props, ref) => {
        const { className, ...other } = props; // 解構 props，允許傳入額外的樣式
        const formControlContext = useFormControlContext(); // 使用上下文取得輸入框狀態
        const [dirty, setDirty] = React.useState(false); // 判斷是否已使用過輸入框

        // 當輸入框已被填寫時，設定 dirty 狀態為 true
        React.useEffect(() => {
            if (formControlContext?.filled) {
                setDirty(true);
            }
        }, [formControlContext]);

        // 如果沒有上下文，不顯示任何輔助文字
        if (formControlContext === undefined) {
            return null;
        }

        const { required, filled } = formControlContext; // 從上下文取得必填與填寫狀態
        const showRequiredError = dirty && required && !filled; // 判斷是否需要顯示錯誤

        return (
            <div className={clsx('text-sm', className)} style={{ height: '0.6rem' }}> {/* 固定高度，避免布局抖動 */}
                {showRequiredError ? (
                    <p ref={ref} className="text-red-500" {...other}>
                        This field is required. {/* 顯示必填錯誤訊息 */}
                    </p>
                ) : (
                    <p ref={ref} className="text-transparent" {...other}>
                        &nbsp; {/* 保留空白區域以維持固定高度 */}
                    </p>
                )}
            </div>
        );
    }
);

// InputField 元件：組合 Label、Input 和 HelperText，形成一個完整的輸入欄位
const InputField: React.FC<InputFieldProps> = ({ label, type = 'text', value, onChange, required }) => {
    return (
        <FormControl required={required} className="mb-4">
            {/* 標籤 */}
            <Label>{label}</Label>
            
            {/* 輸入框 */}
            <Input
                type={type} // 設定輸入框類型，例如 "text" 或 "password"
                placeholder={`Enter your ${label.toLowerCase()}`} // 占位符文字
                slotProps={{
                    input: {
                        value, // 輸入框值
                        onChange, // 當值改變時觸發的事件
                        className: 'w-80 text-sm font-sans font-normal leading-5 px-3 py-2 rounded-lg shadow-md border border-solid border-slate-300', // Tailwind 樣式
                    },
                }}
            />

            {/* 輔助文字 */}
            <HelperText />
        </FormControl>
    );
};

// 匯出 InputField 以供其他元件使用
export default InputField;
