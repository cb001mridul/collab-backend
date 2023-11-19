# REDIS


1. Included redis to reduce latency and also the server is running on multiple workers.

<-------------------------------------------------------------------------------------------------------------------------->

from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy.orm import Session
from . import models
from .database import engine
from . import schemas
from typing import List
from .routers import padmins
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


# models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# origins = ["*"]

# app.add_middleware(

#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],

# )

app.include_router(padmins.router)
# app.include_router(category.router)
# app.include_router(offers.router)
# app.include_router(users.router)
# app.include_router(auth.router)


if __name__ == "__main__":
    # Run the FastAPI application with Gunicorn using 6 workers
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=10)



<----------------------------------------------------------------------------------------------------------------------------->