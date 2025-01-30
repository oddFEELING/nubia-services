import nest_asyncio 
from fastapi import FastAPI

from src.middlewares.register import app_register

nest_asyncio.apply()
app = FastAPI()

app_register(app)

