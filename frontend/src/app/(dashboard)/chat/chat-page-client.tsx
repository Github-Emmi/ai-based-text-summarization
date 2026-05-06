"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PlusCircle } from "lucide-react";
import { toast } from "sonner";

import { listChats } from "@/lib/api/history";
import { SessionCard } from "@/components/chat/session-card";
import { Pagination } from "@/components/history/pagination";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ChatInterface } from "@/components/chat/chat-interface";
import type { ChatSessionSummary, Pagination as PaginationType } from "@/types/api";

function SessionListSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <Skeleton key={i} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  );
}

function ChatPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const summaryId = searchParams.get("summary_id") ?? undefined;

  const [newChat, setNewChat] = useState(!!summaryId);
  const [newSessionId, setNewSessionId] = useState<string | null>(null);

  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listChats({ page, page_size: 10 });
      setSessions(data.items);
      setPagination(data.pagination);
    } catch {
      toast.error("Failed to load chat sessions");
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { void load(); }, [load]);

  function handleSessionCreated(id: string) {
    setNewSessionId(id);
    router.push(`/chat/${id}`);
  }

  function handleDeleted(id: string) {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }

  if (newChat) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="font-semibold">New Chat</h1>
          <Button variant="ghost" size="sm" onClick={() => setNewChat(false)}>
            ← Sessions
          </Button>
        </div>
        <ChatInterface
          sessionId={newSessionId}
          summaryId={summaryId}
          onSessionCreated={handleSessionCreated}
        />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Chat</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Continue a conversation or start a new one.
          </p>
        </div>
        <Button onClick={() => setNewChat(true)}>
          <PlusCircle className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      {loading ? (
        <SessionListSkeleton />
      ) : sessions.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <p className="text-sm">No chat sessions yet.</p>
          <Button className="mt-4" onClick={() => setNewChat(true)}>
            Start your first chat
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <SessionCard key={s.id} session={s} onDeleted={handleDeleted} />
          ))}
        </div>
      )}

      {pagination && (
        <Pagination pagination={pagination} onPageChange={setPage} />
      )}
    </div>
  );
}

export function ChatPageClient() {
  return (
    <Suspense
      fallback={
        <div className="space-y-2 p-6">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      }
    >
      <ChatPageInner />
    </Suspense>
  );
}
