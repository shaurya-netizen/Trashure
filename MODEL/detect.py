from ultralytics import YOLO
import cv2

# Load your trained model
model = YOLO("best.pt")   # make sure best.pt is in same folder

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open camera")
    exit()

print("Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO
    results = model(frame, conf=0.5)

    # Draw detections
    annotated = results[0].plot()

    # Get best detection
    boxes = results[0].boxes
    names = model.names

    best_label = "No Object"
    best_conf = 0.0

    for box in boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = names[cls_id]

        if conf > best_conf:
            best_conf = conf
            best_label = label

    print(f"Detected: {best_label} ({best_conf:.2f})")

    cv2.imshow("YOLO Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()