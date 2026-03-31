from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.bins import router as bins_router
from routes.logs import router as logs_router
from routes.waste import router as waste_router
from routes.upload import router as upload_router
from routes.process_event import router as process_event_router

app = FastAPI(title="Smart Waste Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(bins_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(waste_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(process_event_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Smart Waste Analytics API running"}

@app.get("/api/analytics")
def get_analytics():
    return {
        "message": "Analytics endpoint placeholder",
        "status": "ok"
    }

@app.get("/api/route")
def get_route():
    return {
        "message": "Route optimization endpoint placeholder",
        "status": "ok"
    }