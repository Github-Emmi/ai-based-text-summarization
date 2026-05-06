"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TextInput } from "@/components/summarize/text-input";
import { PdfUpload } from "@/components/summarize/pdf-upload";
import { ResultCard } from "@/components/summarize/result-card";
import { useSummarizeStore } from "@/lib/store/summarize-store";

export default function SummarizePage() {
  const { currentResult } = useSummarizeStore();

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Summarize</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste text or upload a PDF to generate an AI summary.
        </p>
      </div>

      <Tabs defaultValue="text">
        <TabsList>
          <TabsTrigger value="text">Text</TabsTrigger>
          <TabsTrigger value="pdf">PDF</TabsTrigger>
        </TabsList>
        <TabsContent value="text" className="mt-4">
          <TextInput />
        </TabsContent>
        <TabsContent value="pdf" className="mt-4">
          <PdfUpload />
        </TabsContent>
      </Tabs>

      {currentResult && <ResultCard result={currentResult} />}
    </div>
  );
}
