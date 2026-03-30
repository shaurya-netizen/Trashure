from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import math
import uvicorn

app = FastAPI()

# ---------------------------------------------------------------------------
# BIN DATA (Hardcoded Maps + Live Hardware)
# ---------------------------------------------------------------------------
bin_locations = {
    "BIN_001": (28.5355, 77.3910),  # Live ESP32 hardware bin
    "BIN_042": (28.5375, 77.3930),
    "BIN_108": (28.5340, 77.3950),
    "BIN_009": (28.5360, 77.3885),
}

bin_status = {
    "BIN_001": {"fill": 0,  "distance_cm": 0,  "lid_moving": False},
    "BIN_042": {"fill": 85, "distance_cm": 15, "lid_moving": False},
    "BIN_108": {"fill": 42, "distance_cm": 40, "lid_moving": False},
    "BIN_009": {"fill": 15, "distance_cm": 80, "lid_moving": False},
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def distance(a, b) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def optimize_route():
    # 1. Define which bins actually need a pickup
    # We pick bins > 50% full, but ALWAYS include BIN_001 if it's > 20% for the demo
    to_pickup = [
        bin_id for bin_id, status in bin_status.items() 
        if status["fill"] > 50 or (bin_id == "BIN_001" and status["fill"] > 20)
    ]
    
    if not to_pickup:
        return []

    route = []
    # Starting Point: GLA University Noida Campus Area
    current_pos = (28.5355, 77.3910) 
    
    while to_pickup:
        # The Greedy Choice: Find the bin closest to the truck's current position
        nearest = min(
            to_pickup, 
            key=lambda b: math.sqrt(
                (current_pos[0] - bin_locations[b][0])**2 + 
                (current_pos[1] - bin_locations[b][1])**2
            )
        )
        
        route.append({
            "bin": nearest,
            "fill": bin_status[nearest]["fill"],
            "location": list(bin_locations[nearest])
        })
        
        # Move the truck to the bin we just "emptied"
        current_pos = bin_locations[nearest]
        to_pickup.remove(nearest)
        
    return route

# ---------------------------------------------------------------------------
# HARDWARE ENDPOINT (ESP32 -> FastAPI)
# ---------------------------------------------------------------------------
# I added two route decorators so it catches the ping even if you forgot 
# to change the URL in your Arduino code!
@app.post("/update_hardware_fill")
@app.post("/update") 
async def update_fill(request: Request):
    """Receives JSON from the ESP32 Ultrasonic sensor"""
    data = await request.json()
    
    # Extract data, default to BIN_001 if the board doesn't specify
    bin_id = data.get("bin_id", "BIN_001") 
    fill = data.get("fill_percent", 0)
    dist = data.get("distance_cm", 0)
    lid = data.get("lid_moving", False)
    
    if bin_id in bin_status:
        bin_status[bin_id]["fill"] = round(fill, 1)
        bin_status[bin_id]["distance_cm"] = dist
        bin_status[bin_id]["lid_moving"] = lid
        
        status_msg = "MOVING" if lid else "STABLE"
        print(f"📡 Hardware Sync [{bin_id}] -> Fill: {fill}% | Dist: {dist}cm | Lid: {status_msg}")
        return {"status": "success"}
        
    return {"status": "error", "message": "Bin not found"}

# ---------------------------------------------------------------------------
# FRONTEND ENDPOINTS (FastAPI -> Dashboard)
# ---------------------------------------------------------------------------
@app.get("/bins")
def get_bins():
    """Serves the dashboard with formatted data"""
    result = {
        bin_id: {
            "fill": data["fill"],
            "distance_cm": data.get("distance_cm", 0),
            "lid_moving": data.get("lid_moving", False),
            "location": list(bin_locations[bin_id]),
        }
        for bin_id, data in bin_status.items()
    }
    return JSONResponse(result)

@app.get("/route")
def get_route():
    # Pick bins > 40% full; always include BIN_001 (live hardware) if > 20%
    to_pickup = [
        bin_id for bin_id, status in bin_status.items()
        if status["fill"] > 40 or (bin_id == "BIN_001" and status["fill"] > 20)
    ]

    route = []
    # Start the truck at BIN_001 (live hardware bin) — Noida coordinates
    current_pos = bin_locations["BIN_001"]

    while to_pickup:
        # Nearest Neighbor: find the bin closest to the truck's current position
        nearest = min(to_pickup, key=lambda b: math.sqrt(
            (current_pos[0] - bin_locations[b][0])**2 +
            (current_pos[1] - bin_locations[b][1])**2
        ))

        route.append({
            "bin": nearest,
            "fill": bin_status[nearest]["fill"],
            "location": list(bin_locations[nearest])
        })
        current_pos = bin_locations[nearest]
        to_pickup.remove(nearest)

    return route

# ---------------------------------------------------------------------------
# SERVE /public AT ROOT
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory="public", html=True), name="static")

if __name__ == "__main__":
    print("🚀 IoT Server Online! Waiting for Hardware Pings...")
    uvicorn.run(app, host="0.0.0.0", port=8000)