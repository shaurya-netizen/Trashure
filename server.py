from flask import Flask, request, jsonify, render_template
import math

app = Flask(__name__)

# -------------------------------
# STORE RAW LOG DATA
# -------------------------------
data_store = []

# -------------------------------
# BIN STATUS (REAL + STATIC)
# -------------------------------
bin_status = {
    "BIN_01": {"plastic": 0, "paper": 0, "metal": 0, "organic": 0},  # REAL
    "BIN_02": {"plastic": 5, "paper": 3, "metal": 2, "organic": 1},  # STATIC
    "BIN_03": {"plastic": 2, "paper": 6, "metal": 1, "organic": 2},  # STATIC
    "BIN_04": {"plastic": 7, "paper": 1, "metal": 3, "organic": 0}   # STATIC
}

# -------------------------------
# REAL-WORLD LOCATIONS (Delhi example)
# -------------------------------
bin_locations = {
    "BIN_01": (28.6139, 77.2090),  # Connaught Place
    "BIN_02": (28.6145, 77.2105),
    "BIN_03": (28.6155, 77.2080),
    "BIN_04": (28.6165, 77.2115)
}

# -------------------------------
# FILL LEVEL CALCULATION
# -------------------------------
def get_fill_level(bin_data):
    total = sum(bin_data.values())
    return min((total / 20) * 100, 100)

# -------------------------------
# RECEIVE DATA FROM AI (ONLY BIN_01)
# -------------------------------
@app.route("/log", methods=["POST"])
def log_data():
    data = request.json
    data_store.append(data)

    bin_id = "BIN_01"   # FORCE real bin only
    waste = data["waste_type"]

    if waste in bin_status[bin_id]:
        bin_status[bin_id][waste] += 1

    print(f"Updated {bin_id}:", bin_status[bin_id])

    return jsonify({"message": "Data stored"}), 200

# -------------------------------
# GET LOG DATA
# -------------------------------
@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(data_store)

# -------------------------------
# GET BIN STATUS
# -------------------------------
@app.route("/bins", methods=["GET"])
def get_bins():
    result = {}

    for bin_id, data in bin_status.items():
        result[bin_id] = {
            "fill": get_fill_level(data),
            "location": bin_locations[bin_id]
        }

    return jsonify(result)

# -------------------------------
# DISTANCE FUNCTION
# -------------------------------
def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

# -------------------------------
# ROUTE OPTIMIZATION
# -------------------------------
def optimize_route():
    bins = []

    for bin_id, data in bin_status.items():
        fill = get_fill_level(data)

        if fill > 40 or bin_id == "BIN_01":  # threshold
            bins.append((bin_id, fill))

    # prioritize high fill
    bins.sort(key=lambda x: x[1], reverse=True)

    route = []
    current = (28.6139, 77.2090)  # truck start

    while bins:
        nearest = min(
            bins,
            key=lambda x: distance(current, bin_locations[x[0]])
        )

        route.append({
            "bin": nearest[0],
            "fill": nearest[1],
            "location": bin_locations[nearest[0]]
        })

        current = bin_locations[nearest[0]]
        bins.remove(nearest)

    return route

# -------------------------------
# GET ROUTE
# -------------------------------
@app.route("/route", methods=["GET"])
def get_route():
    return jsonify(optimize_route())

# -------------------------------
# DASHBOARD
# -------------------------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)