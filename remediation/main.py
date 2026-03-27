"""Phase 5: Alertmanager webhooks trigger targeted pod deletion via the Kubernetes API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from kubernetes import client, config
from kubernetes.config import ConfigException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aegis Remediation")

_v1: client.CoreV1Api | None = None


def _ensure_k8s() -> client.CoreV1Api:
    global _v1
    if _v1 is None:
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()
        _v1 = client.CoreV1Api()
    return _v1


def _success_log_line(pod_name: str) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    return f"Successfully remediated {pod_name} at {ts}."


@app.post("/alerts")
async def receive_alerts(request: Request) -> dict[str, Any]:
    """Alertmanager v2 webhook: delete firing HighMemoryUsage target pods."""
    body: Any = await request.json()
    text = json.dumps(body, indent=2, default=str)
    print("--- Alertmanager webhook ---")
    print(text)
    print("--- end ---")
    logger.info("Received Alertmanager payload (%d bytes)", len(text))

    alerts = body.get("alerts") or []
    if not isinstance(alerts, list):
        return {"status": "error", "detail": "invalid alerts payload"}

    v1 = _ensure_k8s()
    my_pod = os.environ.get("HOSTNAME", "")
    remediated: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for alert in alerts:
        if not isinstance(alert, dict):
            skipped.append("non-dict alert")
            continue
        if alert.get("status") != "firing":
            continue
        labels = alert.get("labels") or {}
        if not isinstance(labels, dict):
            skipped.append("invalid labels")
            continue
        if labels.get("alertname") != "HighMemoryUsage":
            continue
        namespace = labels.get("namespace")
        pod_name = labels.get("pod")
        if not namespace or not pod_name:
            skipped.append(f"missing namespace/pod: {labels!r}")
            continue
        key = (namespace, pod_name)
        if key in seen:
            continue
        seen.add(key)
        if pod_name == my_pod:
            skipped.append(f"refusing to delete self: {pod_name}")
            continue

        def _delete() -> None:
            v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                grace_period_seconds=30,
            )

        try:
            await asyncio.to_thread(_delete)
            line = _success_log_line(pod_name)
            print(line)
            logger.info(line)
            remediated.append(f"{namespace}/{pod_name}")
        except Exception as exc:  # noqa: BLE001 — surface API errors to response
            msg = f"{namespace}/{pod_name}: {exc}"
            errors.append(msg)
            logger.exception("Delete failed for %s", msg)

    return {
        "status": "ok",
        "remediated": remediated,
        "skipped": skipped,
        "errors": errors,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
