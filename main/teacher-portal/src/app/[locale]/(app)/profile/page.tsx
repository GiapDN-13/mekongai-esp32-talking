"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, User, ShieldCheck, Shield } from "lucide-react";
import { toast } from "sonner";
import { backendFetch, getToken } from "@/lib/api";

interface UserInfo {
  id: number;
  username: string;
  superAdmin: number;
  status: number;
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await backendFetch('/user/info', { token: getToken() || '' });
        setUser(data);
      } catch (err: any) {
        toast.error("Không thể tải thông tin: " + err.message);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Hồ sơ giáo viên</h1>
        <p className="text-muted-foreground">Thông tin tài khoản của bạn.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" /> Thông tin tài khoản
          </CardTitle>
          <CardDescription>Dữ liệu từ hệ thống quản lý.</CardDescription>
        </CardHeader>
        <CardContent>
          {user ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold">{user.username}</h3>
                  <p className="text-sm text-muted-foreground">ID: {user.id}</p>
                </div>
              </div>

              <div className="grid gap-3">
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="text-sm text-muted-foreground">Tên đăng nhập</span>
                  <span className="font-medium">{user.username}</span>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="text-sm text-muted-foreground">Vai trò</span>
                  <Badge variant={user.superAdmin === 1 ? "default" : "outline"} className="flex items-center gap-1">
                    {user.superAdmin === 1 ? <ShieldCheck className="w-3 h-3" /> : <Shield className="w-3 h-3" />}
                    {user.superAdmin === 1 ? "Quản trị viên" : "Giáo viên"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <span className="text-sm text-muted-foreground">Trạng thái</span>
                  <Badge variant={user.status === 1 ? "default" : "destructive"}>
                    {user.status === 1 ? "Hoạt động" : "Bị khoá"}
                  </Badge>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">Không thể tải thông tin tài khoản.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
