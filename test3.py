import cv2
import torch
import time
import numpy as np
from pathlib import Path
from request import attempt_login, send_number_plate_detection_alert, send_vehicle_detection_alert

# Load both models
vehicle_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
vehicle_model.classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

plate_model = torch.hub.load('ultralytics/yolov5', 'custom', path='./best2.pt')
plate_model.conf = 0.4

# Output dir
output_dir = Path("cropped_plates")
output_dir.mkdir(exist_ok=True)

saved_boxes = []

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    if interArea == 0: return 0
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    return interArea / float(boxAArea + boxBArea - interArea)

# Initialize authentication
login_email = "developer@developer1.com"
login_password = "developer1"
auth_token = None

# Attempt login
login_success, login_response = attempt_login(login_email, login_password)
if login_success and isinstance(login_response, dict) and "token" in login_response:
    auth_token = login_response["token"]
    print("Authentication successful!")
else:
    print("Authentication failed! Continuing without API integration.")

# Initialize webcam
cap = cv2.VideoCapture(1)  # Use 0 for default webcam
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

frame_count = 0
print("Press 'q' to quit.")

while True:
    # Capture frame from webcam
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame")
        break

    # Detect vehicles
    results = vehicle_model(frame)
    
    if len(results.xyxy[0]) > 0 and auth_token:
        # Send vehicle detection alert when any vehicle is detected
        send_vehicle_detection_alert(auth_token)

    for *vbox, conf, cls in results.xyxy[0]:
        vx1, vy1, vx2, vy2 = map(int, vbox)
        vehicle_crop = frame[vy1:vy2, vx1:vx2]

        # Run number plate detection inside this vehicle
        plate_results = plate_model(vehicle_crop)

        for *pbox, pconf, pcl in plate_results.xyxy[0]:
            px1, py1, px2, py2 = map(int, pbox)
            confidence = float(pconf)

            # Convert plate coords to full image coords
            gx1, gy1 = vx1 + px1, vy1 + py1
            gx2, gy2 = vx1 + px2, vy1 + py2
            gbox = (gx1, gy1, gx2, gy2)

            if confidence >= 0.92:
                duplicate = False
                for saved in saved_boxes:
                    if iou(gbox, saved) > 0.35:
                        duplicate = True
                        break

                if not duplicate:
                    plate_crop = frame[gy1:gy2, gx1:gx2]
                    timestamp = int(time.time() * 1000)
                    filename = output_dir / f"plate_{timestamp}_{frame_count}.jpg"
                    cv2.imwrite(str(filename), plate_crop)
                    saved_boxes.append(gbox)
                    
                    # Send plate detection alert if authenticated
                    if auth_token:
                        send_number_plate_detection_alert(str(filename), auth_token)

            # Draw plate box on full frame
            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (0, 255, 0), 2)
            cv2.putText(frame, f"{confidence:.2f}", (gx1, gy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    cv2.imshow("Vehicle + Plate Detection", frame)
    frame_count += 1
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
