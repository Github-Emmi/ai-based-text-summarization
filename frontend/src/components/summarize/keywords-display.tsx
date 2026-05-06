import { Badge } from "@/components/ui/badge";

interface KeywordsDisplayProps {
  keywords: string[];
}

export function KeywordsDisplay({ keywords }: KeywordsDisplayProps) {
  if (!keywords.length) return null;

  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
        Keywords
      </p>
      <div className="flex flex-wrap gap-1.5">
        {keywords.map((kw, i) => (
          <Badge key={`${i}-${kw}`} variant="secondary" className="text-xs">
            {kw}
          </Badge>
        ))}
      </div>
    </div>
  );
}
