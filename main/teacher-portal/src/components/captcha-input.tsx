"use client";

import { useState, useImperativeHandle, forwardRef, useRef, useEffect } from "react";
import { Input } from "@/components/ui/input";

let globalCounter = 0;
function generateUUID() {
  globalCounter++;
  return `${Date.now()}-${globalCounter}-${'xxxx'.replace(/x/g, () => ((Math.random() * 16) | 0).toString(16))}`;
}

export interface CaptchaHandle {
  refresh: () => void;
  getCaptchaId: () => string;
}

interface CaptchaInputProps {
  value: string;
  onChange: (value: string) => void;
}

export const CaptchaInput = forwardRef<CaptchaHandle, CaptchaInputProps>(
  function CaptchaInput({ value, onChange }, ref) {
    const idRef = useRef('');
    const [imgUrl, setImgUrl] = useState<string | null>(null);

    function doRefresh() {
      const uuid = generateUUID();
      idRef.current = uuid;
      setImgUrl(`/backend/user/captcha?uuid=${uuid}&t=${Date.now()}`);
      onChange('');
    }

    useEffect(() => {
      doRefresh();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useImperativeHandle(ref, () => ({
      refresh: doRefresh,
      getCaptchaId: () => idRef.current,
    }));

    return (
      <div className="flex gap-3 items-center">
        <Input
          placeholder="Nhập mã bên phải"
          value={value}
          onChange={e => onChange(e.target.value)}
          className="flex-1"
          autoComplete="off"
          required
        />
        <div
          className="h-10 w-28 border rounded-md overflow-hidden cursor-pointer shrink-0 bg-white flex items-center justify-center"
          onClick={doRefresh}
          title="Click để đổi mã mới"
        >
          {imgUrl ? (
            <img
              src={imgUrl}
              alt="captcha"
              className="h-full w-full object-contain"
              onError={() => setTimeout(doRefresh, 500)}
            />
          ) : (
            <span className="text-xs text-muted-foreground">Đang tải...</span>
          )}
        </div>
      </div>
    );
  }
);
