from fastapi import APIRouter
from controllers.waste_controller import get_logs

router = APIRouter()

@router.get("/logs")
def fetch_logs():
    return get_logs()