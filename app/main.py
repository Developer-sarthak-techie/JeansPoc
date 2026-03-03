from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import design_routes

app = FastAPI(title="Jeans Print Engine")

app.include_router(design_routes.router)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")