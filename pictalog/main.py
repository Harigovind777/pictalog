from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pictalog.api import auth_routes, catalogs, files, imports, share, variants, worker
from pictalog.config import Settings
from pictalog.db import Base, make_engine, make_sessionmaker
from pictalog.storage import LocalStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Pictalog", lifespan=lifespan)
    app.state.settings = settings
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.storage = LocalStorage(settings.storage_dir)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    for module in (auth_routes, catalogs, files, imports, share, variants, worker):
        app.include_router(module.router)
    return app
