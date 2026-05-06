import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils/format";
import type { ChatMessage } from "@/types/api";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-2", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-sm"
            : "bg-muted text-foreground rounded-bl-sm"
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p
          className={cn(
            "text-[10px] mt-1",
            isUser ? "text-primary-foreground/60 text-right" : "text-muted-foreground"
          )}
        >
          {formatDate(message.created_at)}
        </p>
      </div>
    </div>
  );
}
