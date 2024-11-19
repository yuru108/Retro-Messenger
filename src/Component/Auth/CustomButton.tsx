import * as React from 'react';
import { Button as BaseButton, ButtonProps } from '@mui/base/Button';
import clsx from 'clsx';

// 按鈕元件
const CustomButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (props, ref) => {
      const { className, children, ...other } = props;
      return (
        <BaseButton
          ref={ref}
          className={clsx(
            'cursor-pointer transition text-sm font-sans font-semibold leading-normal bg-cyan-500 text-white rounded-full px-4 py-2 hover:bg-cyan-600 active:bg-cyan-700 shadow-md focus-visible:outline-none',
            className,
          )}
          {...other}
          >
          {children} {/* 渲染 children */}
        </BaseButton>
      );
    },
  );
  export default CustomButton;