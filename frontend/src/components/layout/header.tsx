"use client";

import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/layout/sidebar";
import { Sheet, SheetContent } from "@/components/ui/sheet";

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <header className="flex h-14 items-center border-b bg-background px-4 gap-3 md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </Button>
        {title && <span className="font-medium text-sm">{title}</span>}
      </header>

      {/* Mobile Drawer */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-64">
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-3 right-3 z-50"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
          <Sidebar onClose={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>
    </>
  );
}
