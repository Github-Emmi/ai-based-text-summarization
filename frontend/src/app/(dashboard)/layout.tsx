import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col flex-shrink-0">
        <Sidebar />
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile header with hamburger */}
        <Header />

        <main className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-zinc-950">
          {children}
        </main>
      </div>
    </div>
  );
}
