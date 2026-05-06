"""Prompt templates for summarization and chat.

Centralizing all prompts prevents drift between services and makes A/B testing easy.
"""

from __future__ import annotations

SUMMARIZE_SYSTEM_PROMPT = """\
You are an expert summarization assistant. Your job is to produce a clear, accurate, \
and concise summary of the provided text.

Rules:
- Preserve the key facts, arguments, and conclusions from the original text
- Do not add information not present in the original
- Use {format_instruction}
- Target length: {length_instruction}
- Language: Respond in the same language as the input text
"""

LENGTH_INSTRUCTIONS: dict[str, str] = {
    "short":  "2-3 sentences (~50-80 words)",
    "medium": "1-2 paragraphs (~100-150 words)",
    "long":   "3-5 paragraphs (~200-350 words)",
}

FORMAT_INSTRUCTIONS: dict[str, str] = {
    "paragraph": "flowing prose paragraphs",
    "bullets":   "bullet points, one key point per line starting with •",
}


def build_summarize_prompt(format: str, length: str) -> str:
    return SUMMARIZE_SYSTEM_PROMPT.format(
        format_instruction=FORMAT_INSTRUCTIONS.get(format, FORMAT_INSTRUCTIONS["paragraph"]),
        length_instruction=LENGTH_INSTRUCTIONS.get(length, LENGTH_INSTRUCTIONS["medium"]),
    )


CHAT_SYSTEM_PROMPT_WITH_DOC = """\
You are a helpful assistant. The user is asking questions about the following document.

--- DOCUMENT SUMMARY ---
{summary}

--- ORIGINAL TEXT (truncated) ---
{original_text}

Answer questions based on the document content above. If the answer is not in the \
document, say so clearly.
"""

CHAT_SYSTEM_PROMPT_GENERIC = "You are a helpful assistant."


def build_chat_prompt(summary: str, original_text: str) -> str:
    return CHAT_SYSTEM_PROMPT_WITH_DOC.format(
        summary=summary,
        original_text=original_text[:8000],
    )
