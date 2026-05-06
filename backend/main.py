"""Development runner for local hot-reload.

Usage (from backend/ with venv activated):
    python main.py

Do NOT use this in production — the Docker entrypoint uses uvicorn directly.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
