from fastapi import FastAPI

from .config import settings
from .routers import org, admin


app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/")
async def root():
    return {"message": "Organization Management Service is running"}


app.include_router(org.router)
app.include_router(admin.router)
