"""Phase 4: receives Alertmanager webhook payloads and logs them for debugging."""

import json
import logging
from typing import Any

from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aegis Remediation")


@app.post("/alerts")
async def receive_alerts(request: Request) -> dict[str, Any]:
    """Alertmanager v2 webhook: JSON body with alerts[], status, receiver, etc."""
    body: Any = await request.json()
    text = json.dumps(body, indent=2, default=str)
    print("--- Alertmanager webhook ---")
    print(text)
    print("--- end ---")
    logger.info("Received Alertmanager payload (%d bytes)", len(text))
    return {"status": "ok", "received": True}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
