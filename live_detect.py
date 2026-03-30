from ultralytics import YOLO
import cv2
import requests
from datetime import datetime

model = YOLO("waste_yolo8s.pt")

valid_map = {

    # 🟦 PLASTIC
    "Plastic bottle": "plastic",
    "Plastic bag": "plastic",
    "Plastic cup": "plastic",
    "Plastic caps": "plastic",
    "Plastic toys": "plastic",
    "Plastic can": "plastic",
    "Plastic canister": "plastic",
    "Plastic shaker": "plastic",
    "Combined plastic": "plastic",
    "Stretch film": "plastic",
    "Zip plastic bag": "plastic",
    "Unknown plastic": "plastic",
    "Container for household chemicals": "plastic",
    "Disposable tableware": "plastic",

    # 🟨 PAPER
    "Cardboard": "paper",
    "Paper": "paper",
    "Paper bag": "paper",
    "Paper cups": "paper",
    "Paper shavings": "paper",
    "Papier mache": "paper",
    "Postal packaging": "paper",
    "Cellulose": "paper",
    "Tetra pack": "paper",

    # 🩶 METAL
    "Aluminum can": "metal",
    "Aluminum caps": "metal",
    "Aerosols": "metal",
    "Foil": "metal",
    "Iron utensils": "metal",
    "Metal shavings": "metal",
    "Scrap metal": "metal",
    "Tin": "metal",

    # 🟩 ORGANIC
    "Organic": "organic"
}

cap = cv2.VideoCapture(0)

# 🔥 cooldown system
last_sent_time = 0
cooldown = 3  # seconds

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera not working ❌")
        break

    # Resize for stability
    frame = cv2.resize(frame, (640, 480))

    results = model(frame, conf=0.4)

    annotated = results[0].plot()

    detected_types = set()

    for box in results[0].boxes:
        cls_name = model.names[int(box.cls)]

        if cls_name in valid_map:
            detected_types.add(valid_map[cls_name])

    # ⏱️ send data only every few seconds
    now = datetime.now().timestamp()

    if detected_types and (now - last_sent_time > cooldown):
        for waste in detected_types:
            data = {
                "bin_id": "BIN_01",
                "waste_type": waste,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            try:
                requests.post("http://127.0.0.1:5000/log", json=data)
                print("Sent:", data)
            except:
                print("Server not running")

        last_sent_time = now

    # ✅ Show window properly
    cv2.imshow("Live Detection", annotated)

    # VERY IMPORTANT
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()