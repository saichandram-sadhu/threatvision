"""ThreatVision API — expanded in Milestone M2."""

from fastapi import FastAPI

app = FastAPI(title="ThreatVision API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
