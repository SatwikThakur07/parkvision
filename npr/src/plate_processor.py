"""License plate detection and recognition processor"""
import cv2
import numpy as np
import re
from typing import Optional, Dict, List, Tuple
from collections import defaultdict, deque
from ultralytics import YOLO
import easyocr
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.log_level, settings.log_dir)


class PlateProcessor:
    """Main processor for license plate detection and recognition"""
    
    def __init__(self):
        """Initialize models and patterns"""
        try:
            logger.info(f"Loading YOLO model from {settings.yolo_model_path}")
            self.model = YOLO(settings.yolo_model_path)
            logger.info("YOLO model loaded successfully")
            
            logger.info("Initializing EasyOCR reader...")
            self.reader = easyocr.Reader(
                settings.ocr_languages_list,
                gpu=settings.ocr_gpu_enabled
            )
            logger.info("EasyOCR reader initialized successfully")
            
            self.plate_pattern = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$")
            self.plate_history = defaultdict(lambda: deque(maxlen=10))
            self.plate_final = {}
            
            # Character mapping for OCR correction
            self.mapping_num_to_alpha = {
                "0": "O", "1": "I", "2": "Z", "3": "E",
                "5": "S", "6": "G", "8": "B"
            }
            self.mapping_alpha_to_num = {
                "O": "0", "I": "1", "Z": "2", "E": "3",
                "S": "5", "G": "6", "B": "8"
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize PlateProcessor: {e}", exc_info=True)
            raise
    
    def correct_plate_format(self, ocr_text: str) -> str:
        """Correct OCR text to match UK plate format"""
        ocr_text = ocr_text.upper().replace(" ", "")
        if len(ocr_text) != 7:
            return ""
        
        corrected = []
        for i, ch in enumerate(ocr_text):
            if i < 2 or i >= 4:  # Letters position
                if ch.isdigit() and ch in self.mapping_num_to_alpha:
                    corrected.append(self.mapping_num_to_alpha[ch])
                elif ch.isalpha():
                    corrected.append(ch)
                else:
                    return ""
            else:  # Numbers position
                if ch.isalpha() and ch in self.mapping_alpha_to_num:
                    corrected.append(self.mapping_alpha_to_num[ch])
                elif ch.isdigit():
                    corrected.append(ch)
                else:
                    return ""
        
        return "".join(corrected)
    
    def recognize_plate(self, plate_crop: np.ndarray) -> str:
        """Recognize text from license plate crop"""
        if plate_crop.size == 0:
            return ""
        
        def normalize(txt: str) -> str:
            return txt.upper().replace(" ", "").strip()

        def clean_and_validate(txt: str) -> str:
            txt = normalize(txt)
            candidate = self.correct_plate_format(txt)
            if candidate and self.plate_pattern.match(candidate):
                return candidate
            return ""

        try:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            plate_resized = cv2.resize(
                thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC
            )

            attempts = [
                plate_resized,
                gray,
                plate_crop,
                cv2.bitwise_not(plate_resized)
            ]

            for variant in attempts:
                ocr_result = self.reader.readtext(
                    variant,
                    detail=0,
                    allowlist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                )
                if len(ocr_result) > 0:
                    for txt in ocr_result:
                        candidate = clean_and_validate(txt)
                        if candidate:
                            return candidate
        
        except Exception as e:
            logger.debug(f"OCR recognition failed: {e}")
        
        return ""
    
    def get_box_id(self, x1: int, y1: int, x2: int, y2: int) -> str:
        """Generate unique box ID for tracking"""
        return f"{int(x1/10)}_{int(y1/10)}_{int(x2/10)}_{int(y2/10)}"
    
    def get_stable_plate(self, box_id: str, new_text: str) -> str:
        """Get stable plate text using history"""
        if new_text:
            self.plate_history[box_id].append(new_text)
            if len(self.plate_history[box_id]) > 0:
                most_common = max(
                    set(self.plate_history[box_id]),
                    key=self.plate_history[box_id].count
                )
                # Require at least 1 (single) observation to emit, but prefer stable when available
                if self.plate_history[box_id].count(most_common) >= 1:
                    self.plate_final[box_id] = most_common
        return self.plate_final.get(box_id, "")
    
    def detect_plates(self, frame: np.ndarray) -> List[Dict]:
        """Detect and recognize plates in a frame"""
        detections = []
        
        try:
            results = self.model(frame, verbose=False)
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = float(box.conf.cpu().numpy()[0])
                    if conf < settings.confidence_threshold:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    plate_crop = frame[y1:y2, x1:x2]
                    
                    text = self.recognize_plate(plate_crop)
                    box_id = self.get_box_id(x1, y1, x2, y2)
                    stable_plate = self.get_stable_plate(box_id, text)
                    
                    if stable_plate:
                        detections.append({
                            "plate_number": stable_plate,
                            "confidence": round(float(conf), 3),
                            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                            "box_id": box_id
                        })
        
        except Exception as e:
            logger.error(f"Error during plate detection: {e}", exc_info=True)
        
        return detections
    
    def annotate_frame(
        self, frame: np.ndarray, detections: List[Dict]
    ) -> np.ndarray:
        """Annotate frame with detected plates"""
        annotated = frame.copy()
        
        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            plate_number = detection["plate_number"]
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # Draw plate crop overlay
            plate_crop = frame[y1:y2, x1:x2]
            if plate_crop.size > 0:
                overlay_h, overlay_w = 150, 400
                plate_resized = cv2.resize(plate_crop, (overlay_w, overlay_h))
                
                oy1 = max(0, y1 - overlay_h - 40)
                ox1 = x1
                oy2, ox2 = oy1 + overlay_h, ox1 + overlay_w
                
                if oy2 <= annotated.shape[0] and ox2 <= annotated.shape[1]:
                    annotated[oy1:oy2, ox1:ox2] = plate_resized
                
                # Draw text
                cv2.putText(
                    annotated, plate_number, (ox1, oy1 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 6
                )
                cv2.putText(
                    annotated, plate_number, (ox1, oy1 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3
                )
        
        return annotated

