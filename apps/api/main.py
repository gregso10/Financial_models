from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import simulation, data

app = FastAPI(title="Immo Invest API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}