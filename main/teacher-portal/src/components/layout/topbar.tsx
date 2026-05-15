"use client";

import { Bell, User, LogOut, Settings, UserCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link, useRouter } from "@/i18n/routing";
import { clearToken, getUser } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Topbar() {
  const router = useRouter();
  const user = getUser();

  const handleLogout = () => {
    clearToken();
    router.push('/login');
  };

  return (
    <header className="h-14 border-b flex items-center justify-between px-6 bg-background">
      <div className="font-semibold text-lg md:hidden text-primary">MekongAI Teacher</div>
      <div className="hidden md:block"></div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon">
          <Bell className="w-5 h-5" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-2 p-1 px-2 h-auto hover:bg-muted rounded-full outline-none cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="w-5 h-5 text-primary" />
            </div>
            <span className="text-sm font-medium hidden sm:block">{user?.username || 'Giáo viên'}</span>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuGroup>
              <DropdownMenuLabel>Tài khoản</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => router.push('/profile')} className="cursor-pointer">
                <UserCircle className="w-4 h-4 mr-2" /> Hồ sơ
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => router.push('/settings')} className="cursor-pointer">
                <Settings className="w-4 h-4 mr-2" /> Cài đặt
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
              <LogOut className="w-4 h-4 mr-2" /> Đăng xuất
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
