"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { listSummaries } from "@/lib/api/history";
import { FilterBar } from "@/components/history/filter-bar";
import { SummaryCard } from "@/components/history/summary-card";
import { Pagination } from "@/components/history/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import type { SummaryResponse, Pagination as PaginationType, SourceType } from "@/types/api";

function SummaryListSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <Skeleton key={i} className="h-36 w-full rounded-lg" />
      ))}
    </div>
  );
}

export default function HistoryPage() {
  const [items, setItems] = useState<SummaryResponse[]>([]);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [sourceType, setSourceType] = useState<SourceType | "all">("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listSummaries({
        page,
        page_size: 10,
        keyword: keyword || undefined,
        source_type: sourceType === "all" ? undefined : sourceType,
      });
      setItems(data.items);
      setPagination(data.pagination);
    } catch {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  }, [page, keyword, sourceType]);

  useEffect(() => { void load(); }, [load]);

  // Reset page when filters change
  function handleKeywordChange(v: string) {
    setKeyword(v);
    setPage(1);
  }
  function handleSourceTypeChange(v: SourceType | "all") {
    setSourceType(v);
    setPage(1);
  }

  function handleDeleted(id: string) {
    setItems((prev) => prev.filter((s) => s.id !== id));
    if (items.length === 1 && page > 1) setPage(page - 1);
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Browse your past summaries.
        </p>
      </div>

      <FilterBar
        keyword={keyword}
        sourceType={sourceType}
        onKeywordChange={handleKeywordChange}
        onSourceTypeChange={handleSourceTypeChange}
      />

      {loading ? (
        <SummaryListSkeleton />
      ) : items.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground">
          <p className="text-sm">No summaries found.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((s) => (
            <SummaryCard key={s.id} summary={s} onDeleted={handleDeleted} />
          ))}
        </div>
      )}

      {pagination && (
        <Pagination pagination={pagination} onPageChange={setPage} />
      )}
    </div>
  );
}
