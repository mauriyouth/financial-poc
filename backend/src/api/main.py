from fastapi import FastAPI
from src.api.endpoints import hello

app = FastAPI()

app.include_router(hello.router)
