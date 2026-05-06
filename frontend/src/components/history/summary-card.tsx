"use client";

import { useState } from "react";
import { Trash2, ExternalLink, Download, MessageSquare } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { deleteSummary, getSummary } from "@/lib/api/history";
import { exportSummary } from "@/lib/api/export";
import { formatShortDate, truncate, formatLabel, sourceTypeLabel } from "@/lib/utils/format";
import type { SummaryResponse } from "@/types/api";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { KeywordsDisplay } from "@/components/summarize/keywords-display";
import { Separator } from "@/components/ui/separator";

interface SummaryCardProps {
  summary: SummaryResponse;
  onDeleted: (id: string) => void;
}

export function SummaryCard({ summary, onDeleted }: SummaryCardProps) {
  const router = useRouter();
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<SummaryResponse | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function openDetail() {
    setDetailOpen(true);
    if (!detail) {
      setLoadingDetail(true);
      try {
        const full = await getSummary(summary.id);
        setDetail(full);
      } catch {
        toast.error("Failed to load detail");
        setDetailOpen(false);
      } finally {
        setLoadingDetail(false);
      }
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteSummary(summary.id);
      onDeleted(summary.id);
      toast.success("Summary deleted");
      setConfirmDelete(false);
    } catch {
      toast.error("Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  async function handleExport() {
    try {
      await exportSummary(summary.id, `summary-${summary.id}.pdf`);
      toast.success("PDF downloaded");
    } catch {
      toast.error("Export failed");
    }
  }

  return (
    <>
      <Card className="hover:shadow-sm transition-shadow">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm leading-relaxed line-clamp-3">
                {truncate(summary.summary, 200)}
              </p>
            </div>
            <div className="flex flex-col gap-1 flex-shrink-0">
              <Badge variant="outline" className="text-xs whitespace-nowrap">
                {sourceTypeLabel(summary.source_type)}
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {formatLabel(summary.format)}
              </Badge>
            </div>
          </div>

          <KeywordsDisplay keywords={summary.keywords.slice(0, 5)} />

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{formatShortDate(summary.created_at)}</span>
            <span>{summary.word_count.toLocaleString()} words</span>
          </div>

          <div className="flex flex-wrap gap-1.5 pt-1">
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={openDetail}>
              <ExternalLink className="mr-1 h-3 w-3" />
              View
            </Button>
            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={handleExport}>
              <Download className="mr-1 h-3 w-3" />
              Export
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs"
              onClick={() => router.push(`/chat?summary_id=${summary.id}`)}
            >
              <MessageSquare className="mr-1 h-3 w-3" />
              Chat
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs text-destructive hover:text-destructive"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 className="mr-1 h-3 w-3" />
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Detail modal */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Summary Detail</DialogTitle>
          </DialogHeader>
          {loadingDetail ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading…</div>
          ) : detail ? (
            <div className="space-y-4 text-sm">
              <p className="leading-relaxed whitespace-pre-line">{detail.summary}</p>
              <Separator />
              <KeywordsDisplay keywords={detail.keywords} />
              {detail.original_text && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1">
                      Original Text
                    </p>
                    <p className="text-xs leading-relaxed text-muted-foreground whitespace-pre-line line-clamp-10">
                      {detail.original_text}
                    </p>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete summary?</DialogTitle>
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
