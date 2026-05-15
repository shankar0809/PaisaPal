from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paisapal.api.routes import router
from paisapal.db.base import Base, engine
from paisapal.db import models as _models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PaisaPal")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")

__all__ = ["app", "_models"]
