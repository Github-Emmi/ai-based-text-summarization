import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Pagination as PaginationType } from "@/types/api";

interface PaginationProps {
  pagination: PaginationType;
  onPageChange: (page: number) => void;
}

export function Pagination({ pagination, onPageChange }: PaginationProps) {
  const { page, total_pages, total_items, page_size } = pagination;
  const from = (page - 1) * page_size + 1;
  const to = Math.min(page * page_size, total_items);

  if (total_pages <= 1) return null;

  return (
    <div className="flex items-center justify-between text-sm text-muted-foreground">
      <span>
        {from}–{to} of {total_items.toLocaleString()}
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="px-2">
          {page} / {total_pages}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          disabled={page >= total_pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
