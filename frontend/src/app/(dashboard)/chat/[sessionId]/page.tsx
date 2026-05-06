"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";

import { getSession } from "@/lib/api/chat";
import { ChatInterface } from "@/components/chat/chat-interface";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChatSessionResponse } from "@/types/api";

export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<ChatSessionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSession(sessionId);
        setSession(data);
      } catch {
        toast.error("Chat session not found");
        router.push("/chat");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [sessionId, router]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 p-4 border-b">
        <Button variant="ghost" size="icon" onClick={() => router.push("/chat")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {loading ? (
          <Skeleton className="h-5 w-48" />
        ) : (
          <h1 className="font-semibold text-sm truncate">
            {session?.title || "Chat Session"}
          </h1>
        )}
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">
          Loading session…
        </div>
      ) : session ? (
        <ChatInterface
          sessionId={session.session_id}
          summaryId={session.summary_id}
          initialMessages={session.messages}
        />
      ) : null}
    </div>
  );
}
