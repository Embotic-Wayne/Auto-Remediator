from fastapi import FastAPI

app = FastAPI(title="SRE Victim App")

# Global bucket used to simulate a memory leak
LEAK_BUCKET: list[str] = []


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


def _generate_leaky_payload() -> str:
    # About 5 MB per call
    return "x" * 5_000_000


@app.get("/leak")
async def trigger_leak() -> dict:
    payload = _generate_leaky_payload()
    LEAK_BUCKET.append(payload)
    return {
        "message": "Allocated additional memory chunk.",
        "current_chunks": len(LEAK_BUCKET),
        "approx_bytes_per_chunk": len(payload),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

