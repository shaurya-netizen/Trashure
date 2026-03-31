from fastapi import APIRouter
from pydantic import BaseModel

from controllers.waste_controller import (
    add_waste_entry,
    simulate_event,
    reset_data
)

router = APIRouter()


# =========================
# REQUEST MODEL
# =========================
class WasteRequest(BaseModel):
    binId: str
    wasteType: str
    fillLevel: int
    imageUrl: str = ""


# =========================
# ADD WASTE (MANUAL / TEST)
# =========================
@router.post("/waste")
def add_waste(data: WasteRequest):
    return add_waste_entry(
        bin_id=data.binId,
        waste_type=data.wasteType,
        fill_level=data.fillLevel,
        image_url=data.imageUrl
    )


# =========================
# SIMULATE EVENT
# =========================
@router.get("/simulate")
def simulate():
    return simulate_event()


# =========================
# RESET DATA
# =========================
@router.get("/reset")
def reset():
    return reset_data()