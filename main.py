import os
import sys
import json
import queue
import threading
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env from project directory
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="Rank & Rent Research System")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class ResearchRequest(BaseModel):
    niche: str
    state: str
    city: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    return (Path(__file__).parent / "static" / "index.html").read_text()


@app.post("/api/run")
async def run_research(request: ResearchRequest):
    update_queue: queue.Queue = queue.Queue()

    def run_pipeline():
        try:
            from src.rank_rent.crew import RankRentPipeline

            pipeline = RankRentPipeline(
                niche=request.niche,
                state=request.state,
                city=request.city or None,
                update_callback=lambda phase, status, data: update_queue.put(
                    {"phase": phase, "status": status, "data": data}
                ),
            )
            pipeline.run()
            update_queue.put({"phase": "done", "status": "complete", "data": "All phases complete!"})
        except Exception as exc:
            update_queue.put({"phase": "error", "status": "error", "data": str(exc)})

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    async def generate():
        loop = asyncio.get_event_loop()
        while True:
            try:
                msg = await loop.run_in_executor(
                    None, lambda: update_queue.get(timeout=20)
                )
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("phase") in ("done", "error"):
                    break
            except queue.Empty:
                # keepalive ping so connection stays open
                yield f"data: {json.dumps({'phase': 'ping', 'status': 'waiting', 'data': ''})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/health")
async def health():
    keys = {
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "semrush": bool(os.getenv("SEMRUSH_API_KEY")),
        "serper": bool(os.getenv("SERPER_API_KEY")),
    }
    return {"status": "ok", "api_keys_loaded": keys}
