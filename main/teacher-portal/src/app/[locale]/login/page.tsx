"use client";

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { Link, useRouter } from '@/i18n/routing';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LanguageSwitcher } from "@/components/language-switcher";
import { CaptchaInput, CaptchaHandle } from "@/components/captcha-input";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { backendFetch, encryptPassword, setToken, setUser } from '@/lib/api';

export default function LoginPage() {
  const t = useTranslations('Auth');
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [captcha, setCaptcha] = useState('');
  const captchaRef = useRef<CaptchaHandle>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) { toast.error("Vui lòng điền đầy đủ thông tin"); return; }
    if (!captcha) { toast.error("Vui lòng nhập mã xác minh"); return; }

    setIsLoading(true);
    try {
      const encrypted = await encryptPassword(password, captcha);
      const captchaId = captchaRef.current?.getCaptchaId() || '';
      const data = await backendFetch('/user/login', {
        method: 'POST',
        body: JSON.stringify({ username, password: encrypted, captchaId }),
      });
      if (data?.token) {
        setToken(data.token);
        setUser({ username });
        toast.success("Đăng nhập thành công!");
        router.push('/');
      } else {
        toast.error("Phản hồi server không có token");
        captchaRef.current?.refresh();
      }
    } catch (err: any) {
      toast.error(err.message || "Đăng nhập thất bại");
      captchaRef.current?.refresh();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-muted/30">
      <div className="absolute top-4 right-6"><LanguageSwitcher /></div>
      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="space-y-2 text-center">
            <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-2xl font-bold text-primary">M</span>
            </div>
            <CardTitle className="text-2xl">{t('welcome')}</CardTitle>
            <CardDescription>MekongAI Teacher Portal</CardDescription>
          </CardHeader>
          <form onSubmit={handleLogin}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Tài khoản</Label>
                <Input id="username" placeholder="Tên đăng nhập" value={username} onChange={e => setUsername(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">{t('password')}</Label>
                <Input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label>Mã xác minh</Label>
                <CaptchaInput ref={captchaRef} value={captcha} onChange={setCaptcha} />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button type="submit" className="w-full text-lg h-12" disabled={isLoading}>
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : t('loginButton')}
              </Button>
              <div className="text-sm text-center text-muted-foreground">
                {t('noAccount')}{" "}
                <Link href="/register" className="text-primary hover:underline font-medium">{t('registerButton')}</Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
