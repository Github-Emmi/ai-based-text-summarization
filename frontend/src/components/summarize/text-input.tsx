"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { summarizeTextSchema, type SummarizeTextFormValues } from "@/lib/utils/validators";
import { summarizeText } from "@/lib/api/summarize";
import { useSummarizeStore } from "@/lib/store/summarize-store";
import type { SummaryFormat, SummaryLength } from "@/types/api";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { FormatSelector } from "@/components/summarize/format-selector";

export function TextInput() {
  const [format, setFormat] = useState<SummaryFormat>("paragraph");
  const [length, setLength] = useState<SummaryLength>("medium");
  const { setResult, setLoading, isLoading } = useSummarizeStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<SummarizeTextFormValues>({
    resolver: zodResolver(summarizeTextSchema),
  });

  async function onSubmit(values: SummarizeTextFormValues) {
    setLoading(true);
    try {
      const result = await summarizeText({
        text: values.text,
        format,
        summary_length: length,
      });
      setResult(result);
      reset();
      toast.success("Summary generated!");
    } catch {
      toast.error("Summarization failed. Please try again.");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="text">Text to summarize</Label>
        <Textarea
          id="text"
          rows={10}
          placeholder="Paste or type your text here (minimum 50 characters)…"
          className="resize-y"
          disabled={isLoading}
          {...register("text")}
        />
        {errors.text && (
          <p className="text-sm text-destructive">{errors.text.message}</p>
        )}
      </div>

      <FormatSelector
        format={format}
        length={length}
        onFormatChange={setFormat}
        onLengthChange={setLength}
        disabled={isLoading}
      />

      <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
        {isLoading ? "Summarizing…" : "Summarize"}
      </Button>
    </form>
  );
}
