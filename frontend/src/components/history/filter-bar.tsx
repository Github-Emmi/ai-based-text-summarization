"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { SourceType } from "@/types/api";

interface FilterBarProps {
  keyword: string;
  sourceType: SourceType | "all";
  onKeywordChange: (v: string) => void;
  onSourceTypeChange: (v: SourceType | "all") => void;
}

export function FilterBar({
  keyword,
  sourceType,
  onKeywordChange,
  onSourceTypeChange,
}: FilterBarProps) {
  const [draft, setDraft] = useState(keyword);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") onKeywordChange(draft);
  }

  function handleBlur() {
    onKeywordChange(draft);
  }

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder="Filter by keyword (press Enter)"
          className="pl-9"
        />
      </div>
      <Select
        value={sourceType}
        onValueChange={(v) => onSourceTypeChange(v as SourceType | "all")}
      >
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Source type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All sources</SelectItem>
          <SelectItem value="text">Text</SelectItem>
          <SelectItem value="pdf">PDF</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
