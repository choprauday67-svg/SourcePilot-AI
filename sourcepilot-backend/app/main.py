from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.infrastructure.db.base import Base, engine
import app.infrastructure.db.models # Ensure all ORM models registered

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS for local Vite development & SPA integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routes
from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_requirements import router as requirements_router
from app.api.v1.routes_suppliers import router as suppliers_router
from app.api.v1.routes_rfq import router as rfq_router
from app.api.v1.routes_quotations import router as quotations_router
from app.api.v1.routes_analytics import router as analytics_router
# Phase 2
from app.api.v1.routes_webhooks import router as webhooks_router
from app.api.v1.routes_comments import router as comments_router
from app.api.v1.routes_connectors import router as connectors_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(requirements_router, prefix=settings.API_V1_STR)
app.include_router(suppliers_router, prefix=settings.API_V1_STR)
app.include_router(rfq_router, prefix=settings.API_V1_STR)
app.include_router(quotations_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
# Phase 2
app.include_router(webhooks_router, prefix=settings.API_V1_STR)
app.include_router(comments_router, prefix=settings.API_V1_STR)
app.include_router(connectors_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
