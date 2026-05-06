"use client";

import { Download, MessageSquare, Copy } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { KeywordsDisplay } from "@/components/summarize/keywords-display";
import { exportSummary } from "@/lib/api/export";
import { formatDate, formatTokens, formatLabel, summaryLengthLabel } from "@/lib/utils/format";
import type { SummaryResponse } from "@/types/api";

interface ResultCardProps {
  result: SummaryResponse;
}

export function ResultCard({ result }: ResultCardProps) {
  const router = useRouter();

  async function handleExport() {
    try {
      await exportSummary(result.id, `summary-${result.id}.pdf`);
      toast.success("PDF downloaded");
    } catch {
      toast.error("Export failed");
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(result.summary);
    toast.success("Copied to clipboard");
  }

  function handleChat() {
    router.push(`/chat?summary_id=${result.id}`);
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <CardTitle className="text-base">Summary</CardTitle>
          <div className="flex gap-1.5 flex-wrap">
            <Badge variant="outline">{formatLabel(result.format)}</Badge>
            <Badge variant="outline">{summaryLengthLabel(result.summary_length)}</Badge>
            <Badge variant="secondary">{result.language.toUpperCase()}</Badge>
            {result.source_type === "pdf" && (
              <Badge variant="secondary">PDF</Badge>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">{formatDate(result.created_at)}</p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary text */}
        <p className="text-sm leading-relaxed whitespace-pre-line">{result.summary}</p>

        <Separator />

        {/* Keywords */}
        <KeywordsDisplay keywords={result.keywords} />

        {/* Stats row */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span>{result.word_count.toLocaleString()} words</span>
          <span>{formatTokens(result.tokens_used)}</span>
          <span className="font-mono">{result.model_used}</span>
          {result.original_filename && (
            <span className="truncate max-w-[200px]">{result.original_filename}</span>
          )}
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={handleCopy}>
            <Copy className="mr-1.5 h-3.5 w-3.5" />
            Copy
          </Button>
          <Button size="sm" variant="outline" onClick={handleExport}>
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Export PDF
          </Button>
          <Button size="sm" onClick={handleChat}>
            <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
            Chat about this
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
