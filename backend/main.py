import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from material_catalog import search_materials
from orchestrator import (
    generate_lockscreen_with_agent_loop,
    stream_lockscreen_with_agent_loop,
)


app = FastAPI(title="LockScreen DSL Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateLockScreenRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/generate-lockscreen")
def generate_lockscreen(request: GenerateLockScreenRequest):
    return generate_lockscreen_with_agent_loop(request.prompt)


@app.post("/api/generate-lockscreen/stream")
def generate_lockscreen_stream(request: GenerateLockScreenRequest):
    def event_stream():
        for event in stream_lockscreen_with_agent_loop(request.prompt):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/materials/search")
def search_material_catalog(q: str = "", limit: int = 8):
    return {
        "items": search_materials({"query": q}, limit=max(1, min(limit, 20))),
    }
