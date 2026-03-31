from fastapi import APIRouter
from controllers.waste_controller import get_bins

router = APIRouter()

@router.get("/bins")
def fetch_bins():
    return get_bins()