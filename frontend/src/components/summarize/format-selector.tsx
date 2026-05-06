"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { SummaryFormat, SummaryLength } from "@/types/api";

interface FormatSelectorProps {
  format: SummaryFormat;
  length: SummaryLength;
  onFormatChange: (v: SummaryFormat) => void;
  onLengthChange: (v: SummaryLength) => void;
  disabled?: boolean;
}

export function FormatSelector({
  format,
  length,
  onFormatChange,
  onLengthChange,
  disabled,
}: FormatSelectorProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <div className="flex-1 space-y-1.5">
        <Label>Format</Label>
        <Select
          value={format}
          onValueChange={(v) => onFormatChange(v as SummaryFormat)}
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="paragraph">Paragraph</SelectItem>
            <SelectItem value="bullets">Bullet Points</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex-1 space-y-1.5">
        <Label>Length</Label>
        <Select
          value={length}
          onValueChange={(v) => onLengthChange(v as SummaryLength)}
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="short">Short</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="long">Long</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
