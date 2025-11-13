import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import users, groups, recommendations, plans
from app import prompt_hub    
from dotenv import load_dotenv
import logging
load_dotenv() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    prompt_hub.langfuse
    logging.getLogger(__name__).info("Application lifespan started")
    yield
    logging.getLogger(__name__).info("Application lifespan ended")

def create_app():
    app = FastAPI(
        title="Trip Planner Backend",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health")
    async def healthcheck():
        return {"status": "ok"}

    app.include_router(users.router, prefix="/api/v1")
    app.include_router(groups.router, prefix="/api/v1")
    app.include_router(recommendations.router, prefix="/api/v1")
    app.include_router(plans.router, prefix="/api/v1")

    logging.getLogger(__name__).info("Routers registered. Backend ready.")
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7878,
        reload=True,
        log_level="info"
    )
