"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.api.routes import router
from backend.knowledge.kb_search import load_knowledge_base
from backend.knowledge.product_info import load_products

app = FastAPI(
    title="Reolink AI Customer Service Agent",
    description="Intelligent customer service agent with Agent Loop architecture",
    version="1.0.0",
)

# CORS
settings = get_settings()
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup():
    """Initialize knowledge base and product catalog on startup."""
    load_knowledge_base()
    load_products()
    print("Knowledge base and product catalog loaded.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
