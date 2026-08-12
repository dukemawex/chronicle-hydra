from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
from chronicle import HydraClient

app = FastAPI(title="Chronicle", version="0.1.0")

@app.get("/", response_class=HTMLResponse)
async def home():
    return Path("static/index.html").read_text()
client = HydraClient()

class Query(BaseModel):
    subject: str
    predicate: str

@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "chronicle"}

@app.post("/demo/setup")
async def setup():
    try:
        await client.setup_demo()
        return {"ok": True, "message": "Demo graph loaded"}
    except Exception as e:
        raise HTTPException(502, f"HydraDB unavailable: {e}")

@app.post("/memory/current")
async def current(q: Query):
    try:
        return await client.current_assertion(q.subject, q.predicate)
    except Exception as e:
        raise HTTPException(502, f"HydraDB unavailable: {e}")

@app.post("/memory/history")
async def history(q: Query):
    try:
        return await client.history(q.subject, q.predicate)
    except Exception as e:
        raise HTTPException(502, f"HydraDB unavailable: {e}")

@app.post("/memory/abstain")
async def abstain(q: Query):
    try:
        return await client.abstain(q.subject, q.predicate)
    except Exception as e:
        raise HTTPException(502, f"HydraDB unavailable: {e}")
