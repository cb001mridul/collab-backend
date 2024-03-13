from fastapi import FastAPI
from .routers import padmins, contributor, projects, auth, users
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(padmins.router)
app.include_router(contributor.router)
app.include_router(projects.router)
app.include_router(auth.router)
app.include_router(users.router)

# This section will be executed if the script is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=4)
