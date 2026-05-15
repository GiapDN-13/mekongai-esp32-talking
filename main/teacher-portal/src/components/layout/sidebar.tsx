"use client";

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { usePathname } from '@/i18n/routing';
import { LayoutDashboard, Cpu, BookOpen, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { id: "dashboard", href: "/", icon: LayoutDashboard },
  { id: "devices", href: "/devices", icon: Cpu },
  { id: "knowledge", href: "/knowledge", icon: BookOpen },
  { id: "insights", href: "/insights", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const t = useTranslations('Navigation');

  return (
    <aside className="w-64 border-r bg-muted/30 hidden md:block">
      <div className="h-full flex flex-col">
        <div className="h-14 flex items-center border-b px-6 font-semibold text-lg text-primary">
          MekongAI Teacher
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground font-medium shadow-sm"
                    : "hover:bg-muted text-muted-foreground hover:text-foreground"
                )}
              >
                <item.icon className="w-5 h-5" />
                {t(item.id)}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
