import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import re
import json
import csv
from datetime import datetime
from collections import defaultdict, deque

model=YOLO("license_plate_best.pt")
reader=easyocr.Reader(["en"],gpu=True)

plate_pattern=re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$")

def correct_plate_format(ocr_text):
    mapping_num_to_alpha={"0":"O","1":"I","2":"Z","3":"E","5":"S","6":"G","8":"B"}
    mapping_alpha_to_num={"O":"0","I":"1","Z":"2","E":"3","S":"5","G":"6","B":"8"}

    ocr_text=ocr_text.upper().replace(" ","")
    if len(ocr_text)!=7:
        return ""

    corrected=[]
    for i,ch in enumerate(ocr_text):
        if i<2 or i>=4:
            if ch.isdigit() and ch in mapping_num_to_alpha:
                corrected.append(mapping_num_to_alpha[ch])
            elif ch.isalpha():
                corrected.append(ch)
            else:
                return ""
        else:
            if ch.isalpha() and ch in mapping_alpha_to_num:
                corrected.append(mapping_alpha_to_num[ch])
            elif ch.isdigit():
                corrected.append(ch)
            else:
                return ""

    return "".join(corrected)

def recognize_plate(plate_crop):
    if plate_crop.size ==0:
        return ""
    
    gray=cv2.cvtColor(plate_crop,cv2.COLOR_BGR2GRAY)
    _,thresh=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    plate_resized=cv2.resize(thresh,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)

    try:
        ocr_result=reader.readtext(plate_resized,detail=0,allowlist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if len(ocr_result)>0:
            candidate=correct_plate_format(ocr_result[0])
            if candidate and plate_pattern.match(candidate):
                return candidate

    except:
        pass

    return ""

plate_history=defaultdict(lambda: deque(maxlen=10))
plate_final={}
def get_box_id(x1,y1,x2,y2):
    return f"{int(x1/10)}_{int(y1/10)}_{int(x2/10)}_{int(y2/10)}"

def get_stable_plate(box_id,new_text):
    if new_text:
        plate_history[box_id].append(new_text)
        most_common=max(set(plate_history[box_id]),key=plate_history[box_id].count)
        plate_final[box_id]=most_common
    return plate_final.get(box_id,"")

input_video="cars_plate_video.mp4"
output_video="output_video.mp4"

cap=cv2.VideoCapture(input_video)
fourcc=cv2.VideoWriter_fourcc(*"mp4v")
out=cv2.VideoWriter(output_video,fourcc,cap.get(cv2.CAP_PROP_FPS),(int(cap.get(3)),int(cap.get(4))))

CONF_THRESH=0.3

# Store all detected plates
detected_plates = []
frame_number = 0
fps = cap.get(cv2.CAP_PROP_FPS)

while cap.isOpened():
    ret,frame=cap.read()
    if not ret:
        break
    
    frame_number += 1
    timestamp = frame_number / fps if fps > 0 else 0

    results=model(frame, verbose=False)

    for r in results:
        boxes=r.boxes
        for box in boxes:
            conf=float(box.conf.cpu().numpy()[0])
            if conf < CONF_THRESH:
                continue

            x1,y1,x2,y2=map(int,box.xyxy[0].cpu().numpy())
            plate_crop=frame[y1:y2,x1:x2]

            text=recognize_plate(plate_crop)

            box_id=get_box_id(x1,y1,x2,y2)
            stable_plate=get_stable_plate(box_id,text)
            
            # Store detected plate if it's stable and valid
            if stable_plate:
                detected_plates.append({
                    "plate_number": stable_plate,
                    "frame_number": frame_number,
                    "timestamp_seconds": round(timestamp, 2),
                    "confidence": round(float(conf), 3),
                    "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                    "detection_time": datetime.now().isoformat()
                })
            
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),3)

            if plate_crop.size >0:
                overlay_h,overlay_w=150,400
                plate_resized=cv2.resize(plate_crop,(overlay_w,overlay_h))

                oy1=max(0,y1 - overlay_h -40)
                ox1=x1
                oy2,ox2=oy1+overlay_h,ox1+overlay_w

                if oy2<=frame.shape[0] and ox2<=frame.shape[1]:
                    frame[oy1:oy2,ox1:ox2]=plate_resized

            if stable_plate:
                cv2.putText(frame,stable_plate,(ox1,oy1-20),cv2.FONT_HERSHEY_SIMPLEX,2,(0,0,0),6)
                cv2.putText(frame,stable_plate,(ox1,oy1-20),cv2.FONT_HERSHEY_SIMPLEX,2,(255,255,255),3)

    out.write(frame)
    cv2.imshow("Annotaded Video",frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

# Save detected plates to JSON file
output_json = "detected_plates.json"
with open(output_json, 'w') as f:
    json.dump({
        "total_detections": len(detected_plates),
        "unique_plates": len(set(plate["plate_number"] for plate in detected_plates)),
        "detections": detected_plates
    }, f, indent=2)

# Save detected plates to CSV file
output_csv = "detected_plates.csv"
if detected_plates:
    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["plate_number", "frame_number", "timestamp_seconds", "confidence", "x1", "y1", "x2", "y2", "detection_time"])
        writer.writeheader()
        for plate in detected_plates:
            writer.writerow({
                "plate_number": plate["plate_number"],
                "frame_number": plate["frame_number"],
                "timestamp_seconds": plate["timestamp_seconds"],
                "confidence": plate["confidence"],
                "x1": plate["bbox"]["x1"],
                "y1": plate["bbox"]["y1"],
                "x2": plate["bbox"]["x2"],
                "y2": plate["bbox"]["y2"],
                "detection_time": plate["detection_time"]
            })

print(f"\n✓ Detected {len(detected_plates)} plate readings")
print(f"✓ Found {len(set(plate['plate_number'] for plate in detected_plates))} unique plates")
print(f"✓ Saved to {output_json} and {output_csv}")

        