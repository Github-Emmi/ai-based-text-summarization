"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  FileText,
  History,
  MessageSquare,
  User,
  LogOut,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth-store";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { href: "/summarize", label: "Summarize", icon: Zap },
  { href: "/history", label: "History", icon: History },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/profile", label: "Profile", icon: User },
];

export function Sidebar({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);

  async function handleLogout() {
    clearAuth();
    await fetch("/api/auth/clear-cookie", { method: "POST" });
    toast.success("Signed out");
    router.push("/login");
  }

  return (
    <div className="flex h-full flex-col bg-sidebar border-r">
      {/* Logo */}
      <div className="flex h-14 items-center px-4">
        <Link
          href="/summarize"
          className="flex items-center gap-2 font-semibold text-foreground"
          onClick={onClose}
        >
          <FileText className="h-5 w-5 text-primary" />
          <span>AI Summarizer</span>
        </Link>
      </div>

      <Separator />

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active =
            pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <Separator />

      {/* Logout */}
      <div className="p-4">
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-destructive"
          onClick={handleLogout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </Button>
      </div>
    </div>
  );
}
