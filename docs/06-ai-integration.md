# 07 — AI Integration

## Overview

The AI layer has two components: a **primary** OpenAI GPT-4o-mini service and a **fallback** HuggingFace BART service. A routing layer (`app/ai/router.py`) selects the correct provider transparently. All AI calls are async, include retry logic with exponential backoff, and are instrumented with token usage logging.

---

## AI Architecture Flow

```
SummarizerService / ChatService
         │
         ▼
    AIRouter.route(text, task)
         │
         ├──[Primary]──► OpenAIClient.complete(prompt)
         │                   ├── model: gpt-4o-mini
         │                   ├── retry: 3x, backoff: 1s/2s/4s
         │                   ├── timeout: 30s
         │                   └── returns: AIResponse(text, tokens_used, model)
         │
         └──[Fallback on APIError]──► HuggingFaceClient.complete(text)
                                          ├── model: facebook/bart-large-cnn
                                          ├── source: HF Inference API (dev)
                                          │          local pipeline (prod)
                                          └── returns: AIResponse(text, model)
```

---

## 1. OpenAI Client (`app/ai/openai_client.py`)

### Implementation

```python
import asyncio
import openai
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

client = openai.AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=30.0,
    max_retries=3,
)

async def openai_complete(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> dict:
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,          # gpt-4o-mini
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return {
        "text": response.choices[0].message.content,
        "model": response.model,
        "tokens_used": response.usage.total_tokens,
    }
```

### Key Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `OPENAI_API_KEY` | — | Required. `sk-...` from platform.openai.com |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model ID |
| `OPENAI_MAX_TOKENS` | `1024` | Max tokens in completion |
| `OPENAI_TEMPERATURE` | `0.3` | Lower = more deterministic summaries |

### Cost Reference (GPT-4o-mini)

| Direction | Price (approx.) |
|-----------|-----------------|
| Input tokens | $0.15 / 1M tokens |
| Output tokens | $0.60 / 1M tokens |

For a 1,000-word document → ~1,300 input tokens + ~300 output tokens ≈ **$0.0004 per summary**.

---

## 2. HuggingFace Client (`app/ai/huggingface_client.py`)

Two modes are supported, controlled by `USE_LOCAL_MODEL` env var:

### Mode A — HuggingFace Inference API (Development / Default)

```python
import httpx
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

INFERENCE_URL = (
    "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
)

async def hf_api_complete(text: str, max_length: int = 150, min_length: int = 40) -> dict:
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}"}
    payload = {
        "inputs": text[:1024],   # BART max input: 1024 tokens
        "parameters": {
            "max_length": max_length,
            "min_length": min_length,
            "do_sample": False,
        },
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(INFERENCE_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return {
            "text": result[0]["summary_text"],
            "model": "facebook/bart-large-cnn",
            "tokens_used": None,  # HF API doesn't return token counts
        }
```

### Mode B — Local Pipeline (Production / `USE_LOCAL_MODEL=true`)

```python
from transformers import pipeline
import asyncio
from functools import partial

_pipe = None

def get_pipeline():
    global _pipe
    if _pipe is None:
        _pipe = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1,   # CPU; change to 0 for GPU
        )
    return _pipe

async def hf_local_complete(text: str, max_length: int = 150) -> dict:
    loop = asyncio.get_event_loop()
    pipe = get_pipeline()
    # Run blocking pipeline in a thread pool to avoid blocking the event loop
    result = await loop.run_in_executor(
        None,
        partial(pipe, text[:1024], max_length=max_length, min_length=40, do_sample=False)
    )
    return {
        "text": result[0]["summary_text"],
        "model": "facebook/bart-large-cnn-local",
        "tokens_used": None,
    }
```

### HuggingFace Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `HUGGINGFACE_MODEL` | `facebook/bart-large-cnn` | Model name |
| `HUGGINGFACE_API_TOKEN` | — | HF token for Inference API (free tier) |
| `USE_LOCAL_MODEL` | `false` | `true` = download and run locally |

> **Memory note**: `facebook/bart-large-cnn` requires ~1.6GB RAM. Ensure your Render plan or Docker host has enough memory if running locally.

---

## 3. AI Router (`app/ai/router.py`)

```python
from app.ai.openai_client import openai_complete
from app.ai.huggingface_client import hf_api_complete, hf_local_complete
from app.core.config import settings
from app.core.logging import get_logger
import openai

logger = get_logger(__name__)

async def route_summarize(
    system_prompt: str,
    text: str,
    max_tokens: int,
) -> dict:
    # Try primary: OpenAI
    if settings.OPENAI_API_KEY:
        try:
            result = await openai_complete(system_prompt, text, max_tokens)
            logger.info(f"Summarization via OpenAI: {result['tokens_used']} tokens")
            return result
        except openai.APIError as e:
            logger.warning(f"OpenAI failed, falling back to HuggingFace: {e}")

    # Fallback: HuggingFace
    try:
        if settings.USE_LOCAL_MODEL:
            result = await hf_local_complete(text)
        else:
            result = await hf_api_complete(text)
        logger.info(f"Summarization via HuggingFace fallback: {result['model']}")
        return result
    except Exception as e:
        logger.error(f"HuggingFace fallback also failed: {e}")
        raise RuntimeError("All AI services are unavailable") from e
```

---

## 4. Prompt Templates (`app/ai/prompts.py`)

Centralizing all prompts prevents drift between services and enables easy A/B testing.

### Summarization System Prompt

```python
SUMMARIZE_SYSTEM_PROMPT = """You are an expert summarization assistant. Your job is to produce a clear, accurate, and concise summary of the provided text.

Rules:
- Preserve the key facts, arguments, and conclusions from the original text
- Do not add information not present in the original
- Use {format_instruction}
- Target length: {length_instruction}
- Language: Respond in the same language as the input text

Format instructions mapping:
  paragraph → Write in flowing prose paragraphs
  bullets   → Use bullet points, one key point per line starting with •
"""

LENGTH_INSTRUCTIONS = {
    "short":  "2-3 sentences (~50-80 words)",
    "medium": "1-2 paragraphs (~100-150 words)",
    "long":   "3-5 paragraphs (~200-350 words)",
}

def build_summarize_prompt(format: str, length: str) -> str:
    return SUMMARIZE_SYSTEM_PROMPT.format(
        format_instruction=f"{'bullet points' if format == 'bullets' else 'prose paragraphs'}",
        length_instruction=LENGTH_INSTRUCTIONS.get(length, LENGTH_INSTRUCTIONS["medium"]),
    )
```

### Chat System Prompt

```python
CHAT_SYSTEM_PROMPT = """You are a helpful document assistant. You have access to the following document summary and original text.

Document Summary:
{summary}

Original Text (for reference):
{original_text}

Answer the user's questions based on this document. Be accurate and cite specific parts when relevant. If the answer is not in the document, say so clearly."""

def build_chat_prompt(summary: str, original_text: str) -> str:
    # Truncate original text to avoid exceeding context window
    truncated = original_text[:8000] if len(original_text) > 8000 else original_text
    return CHAT_SYSTEM_PROMPT.format(summary=summary, original_text=truncated)
```

---

## 5. Datasets (Model Training Reference)

If fine-tuning a custom model (advanced/optional), these HuggingFace datasets provide text-summary pairs:

| Dataset | Domain | Size | HF Hub Path |
|---------|--------|------|-------------|
| CNN/DailyMail | News articles | ~300k pairs | `cnn_dailymail` |
| XSum | BBC news (abstractive) | ~227k pairs | `xsum` |
| BillSum | US legislation | ~23k pairs | `billsum` |
| ArXiv | Scientific papers | ~215k pairs | `arxiv_summarization` |

### Load a Dataset

```python
from datasets import load_dataset

# Example: CNN/DailyMail
dataset = load_dataset("cnn_dailymail", "3.0.0")
train_data = dataset["train"]
# Fields: article (input), highlights (target summary)
```

### Fine-Tuning Command (Reference Only)

```bash
# Using Hugging Face Transformers Trainer API
python fine_tune.py \
  --model_name facebook/bart-large-cnn \
  --dataset cnn_dailymail \
  --output_dir ./models/bart-summarizer-finetuned \
  --num_train_epochs 3 \
  --per_device_train_batch_size 4
```

> Fine-tuned models are deployed as local pipelines by setting `USE_LOCAL_MODEL=true` and pointing `HUGGINGFACE_MODEL` to the checkpoint path.

---

## 6. AI Integration Error Handling

| Scenario | Behavior |
|----------|---------|
| `OPENAI_API_KEY` not set | Skip OpenAI, go directly to HuggingFace |
| OpenAI `AuthenticationError` | Log error, fall back to HuggingFace |
| OpenAI `RateLimitError` | Log error, fall back to HuggingFace |
| OpenAI `APITimeoutError` | Log error after 30s, fall back to HuggingFace |
| HuggingFace API timeout | Raise `AIServiceUnavailableError` → 503 response |
| HuggingFace model loading fails | Raise `AIServiceUnavailableError` → 503 response |
| Both fail | 503 response with `AI_SERVICE_UNAVAILABLE` error code |

---

## 7. Token Counting Strategy

For `summary_length` control, map lengths to `max_tokens`:

| `summary_length` | `max_tokens` sent to OpenAI |
|-----------------|---------------------------|
| `short` | 150 |
| `medium` | 400 |
| `long` | 900 |

For HuggingFace BART, map to `max_length` (BART token units, not GPT tokens):

| `summary_length` | BART `max_length` | BART `min_length` |
|-----------------|-------------------|-------------------|
| `short` | 80 | 30 |
| `medium` | 150 | 60 |
| `long` | 300 | 120 |
