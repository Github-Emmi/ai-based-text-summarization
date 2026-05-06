"use client";

import { Trash2, MessageSquare } from "lucide-react";
import Link from "next/link";
import { formatShortDate, truncate } from "@/lib/utils/format";
import type { ChatSessionSummary } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useState } from "react";
import { deleteSession } from "@/lib/api/chat";
import { toast } from "sonner";

interface SessionCardProps {
  session: ChatSessionSummary;
  onDeleted: (id: string) => void;
}

export function SessionCard({ session, onDeleted }: SessionCardProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteSession(session.id);
      onDeleted(session.id);
      toast.success("Chat session deleted");
    } catch {
      toast.error("Delete failed");
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  return (
    <>
      <Card className="hover:shadow-sm transition-shadow">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <Link href={`/chat/${session.id}`}>
                <p className="font-medium text-sm hover:text-primary transition-colors truncate">
                  {truncate(session.title || "Untitled chat", 60)}
                </p>
              </Link>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  <MessageSquare className="mr-1 h-3 w-3" />
                  {session.message_count} messages
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatShortDate(session.updated_at)}
                </span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete chat session?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">This action cannot be undone.</p>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
