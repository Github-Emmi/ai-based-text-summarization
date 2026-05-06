"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { toast } from "sonner";

import { sendMessage } from "@/lib/api/chat";
import type { ChatMessage, SendMessageResponse } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "@/components/chat/message-bubble";

interface ChatInterfaceProps {
  sessionId: string | null;
  summaryId?: string;
  initialMessages?: ChatMessage[];
  onSessionCreated?: (sessionId: string) => void;
}

export function ChatInterface({
  sessionId: initialSessionId,
  summaryId,
  initialMessages = [],
  onSessionCreated,
}: ChatInterfaceProps) {
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    // Optimistic user message
    const optimisticMsg: ChatMessage = {
      id: `opt-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);
    setInput("");
    setSending(true);

    try {
      const res: SendMessageResponse = await sendMessage({
        message: text,
        session_id: sessionId ?? undefined,
        summary_id: summaryId,
      });

      if (!sessionId) {
        setSessionId(res.session_id);
        onSessionCreated?.(res.session_id);
      }

      const assistantMsg: ChatMessage = {
        id: res.message_id,
        role: "assistant",
        content: res.reply,
        tokens_used: res.tokens_used,
        created_at: res.created_at,
      };
      // Replace optimistic with confirmed + add reply
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticMsg.id),
        { ...optimisticMsg, id: `usr-${res.message_id}` },
        assistantMsg,
      ]);
    } catch {
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
      setInput(text);
      toast.error("Failed to send message. Please try again.");
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            Start the conversation…
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {sending && (
              <div className="flex gap-2 justify-start">
                <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm text-muted-foreground animate-pulse">
                  Thinking…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="resize-none flex-1"
            disabled={sending}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || sending}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
