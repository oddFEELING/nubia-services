from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.__router__ import app_router


def app_register(app: FastAPI):
    # ################################################
    # ### Cors
    # #################################################
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ################################################
    # ### Attach routes
    # ################################################
    app.include_router(app_router)
