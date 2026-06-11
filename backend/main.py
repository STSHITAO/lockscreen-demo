from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llm_client import generate_lockscreen_dsl


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
    return generate_lockscreen_dsl(request.prompt)
