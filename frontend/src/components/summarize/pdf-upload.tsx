"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X } from "lucide-react";
import { toast } from "sonner";

import { summarizePdf } from "@/lib/api/summarize";
import { useSummarizeStore } from "@/lib/store/summarize-store";
import type { SummaryFormat, SummaryLength } from "@/types/api";

import { Button } from "@/components/ui/button";
import { FormatSelector } from "@/components/summarize/format-selector";

const MAX_SIZE_MB = 10;

export function PdfUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<SummaryFormat>("paragraph");
  const [length, setLength] = useState<SummaryLength>("medium");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { setResult, setLoading, isLoading } = useSummarizeStore();

  function handleFile(f: File) {
    if (f.type !== "application/pdf") {
      toast.error("Only PDF files are supported.");
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(`File must be under ${MAX_SIZE_MB} MB.`);
      return;
    }
    setFile(f);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }

  async function handleSubmit() {
    if (!file) return;
    setLoading(true);
    try {
      const result = await summarizePdf(file, { format, summary_length: length });
      setResult(result);
      setFile(null);
      toast.success("PDF summarized!");
    } catch {
      toast.error("PDF summarization failed. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          relative flex flex-col items-center justify-center gap-3
          rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors
          ${dragging ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"}
          ${isLoading ? "pointer-events-none opacity-50" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        {file ? (
          <>
            <FileText className="h-8 w-8 text-primary" />
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium truncate max-w-[260px]">{file.name}</span>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <span className="text-xs text-muted-foreground">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </>
        ) : (
          <>
            <Upload className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground text-center">
              Drag and drop a PDF here, or{" "}
              <span className="text-primary font-medium">click to browse</span>
            </p>
            <p className="text-xs text-muted-foreground">Max {MAX_SIZE_MB} MB</p>
          </>
        )}
      </div>

      <FormatSelector
        format={format}
        length={length}
        onFormatChange={setFormat}
        onLengthChange={setLength}
        disabled={isLoading || !file}
      />

      <Button
        onClick={handleSubmit}
        disabled={!file || isLoading}
        className="w-full sm:w-auto"
      >
        {isLoading ? "Summarizing…" : "Summarize PDF"}
      </Button>
    </div>
  );
}
