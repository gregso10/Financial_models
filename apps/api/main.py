"""
Immo Invest API - French Real Estate Investment Analysis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import simulation, data

app = FastAPI(
    title="Immo Invest API",
    description="French real estate investment analysis with LMNP optimization",
    version="0.1.0",
)

# CORS - tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "name": "Immo Invest API",
        "docs": "/docs",
        "endpoints": {
            "simple_simulation": "POST /api/v1/simulate/simple",
            "expert_simulation": "POST /api/v1/expert/simulate",
            "fiscal_compare": "POST /api/v1/expert/fiscal/compare",
            "lmp_check": "GET /api/v1/expert/fiscal/lmp-check",
            "locations": "GET /api/v1/data/locations",
        }
    }