"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2, Save, KeyRound, Globe } from "lucide-react";
import { backendFetch, encryptPassword, getToken } from "@/lib/api";

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Vui lòng điền đầy đủ thông tin");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Mật khẩu mới không khớp");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("Mật khẩu mới phải có ít nhất 6 ký tự");
      return;
    }
    setIsLoading(true);
    try {
      const encCurrent = await encryptPassword(currentPassword);
      const encNew = await encryptPassword(newPassword);
      await backendFetch('/user/change-password', {
        method: 'PUT',
        body: JSON.stringify({ password: encCurrent, newPassword: encNew }),
        token: getToken() || '',
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast.success("Đã đổi mật khẩu thành công!");
    } catch (err: any) {
      toast.error(err.message || "Đổi mật khẩu thất bại");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Cài đặt</h1>
        <p className="text-muted-foreground">Quản lý tài khoản và thiết lập hệ thống.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><KeyRound className="w-5 h-5" /> Đổi mật khẩu</CardTitle>
          <CardDescription>Cập nhật mật khẩu để bảo vệ tài khoản.</CardDescription>
        </CardHeader>
        <form onSubmit={handleChangePassword}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">Mật khẩu hiện tại</Label>
              <Input id="currentPassword" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newPassword">Mật khẩu mới</Label>
              <Input id="newPassword" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Xác nhận mật khẩu mới</Label>
              <Input id="confirmPassword" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
              Đổi mật khẩu
            </Button>
          </CardContent>
        </form>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Globe className="w-5 h-5" /> Ngôn ngữ</CardTitle>
          <CardDescription>Thay đổi ngôn ngữ hiển thị.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button variant="default" onClick={() => { window.location.href = '/vi/settings'; toast.success("Đã chuyển sang Tiếng Việt"); }}>
            Tiếng Việt
          </Button>
          <Button variant="outline" onClick={() => { window.location.href = '/en/settings'; toast.success("Switched to English"); }}>
            English
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
