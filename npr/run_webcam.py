"""Webcam runner for license plate detection"""
import cv2
import json
import csv
import time
from datetime import datetime
from pathlib import Path

from src.plate_processor import PlateProcessor
from src.config import settings
from src.logger import setup_logger


logger = setup_logger(__name__, settings.log_level, settings.log_dir)


def save_detections(detections, output_base: Path):
    """Save detections to JSON and CSV"""
    json_path = output_base.with_suffix(".json")
    csv_path = output_base.with_suffix(".csv")

    # JSON
    with open(json_path, "w") as f:
        json.dump(
            {
                "total_detections": len(detections),
                "unique_plates": len(set(d["plate_number"] for d in detections)),
                "detections": detections,
            },
            f,
            indent=2,
        )

    # CSV
    if detections:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "plate_number",
                    "timestamp_seconds",
                    "frame_number",
                    "confidence",
                    "x1",
                    "y1",
                    "x2",
                    "y2",
                    "detection_time",
                ],
            )
            writer.writeheader()
            for d in detections:
                writer.writerow(
                    {
                        "plate_number": d["plate_number"],
                        "timestamp_seconds": d["timestamp_seconds"],
                        "frame_number": d["frame_number"],
                        "confidence": d["confidence"],
                        "x1": d["bbox"]["x1"],
                        "y1": d["bbox"]["y1"],
                        "x2": d["bbox"]["x2"],
                        "y2": d["bbox"]["y2"],
                        "detection_time": d["detection_time"],
                    }
                )
    return str(json_path), str(csv_path)


def main():
    processor = PlateProcessor()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Could not open webcam (device 0).")
        print("❌ Could not open webcam. Please ensure a camera is connected and accessible.")
        return

    # Video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Output paths
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video = Path(settings.output_dir) / f"webcam_output_{ts}.mp4"
    output_base = Path(settings.output_dir) / f"webcam_detections_{ts}"
    csv_path = output_base.with_suffix(".csv")
    json_path = output_base.with_suffix(".json")
    jsonl_path = output_base.with_suffix(".jsonl")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))

    detections = []
    frame_number = 0
    
    # Initialize incremental file writing
    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "plate_number",
            "timestamp_seconds",
            "frame_number",
            "confidence",
            "x1",
            "y1",
            "x2",
            "y2",
            "detection_time",
        ],
    )
    csv_writer.writeheader()
    
    # Open JSONL file for incremental writing
    jsonl_file = open(jsonl_path, "w")

    logger.info("Starting webcam capture. Press 'q' to stop.")
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("No frame received from webcam. Stopping.")
                break

            frame_number += 1
            timestamp_seconds = round(time.time() - start_time, 2)

            dets = processor.detect_plates(frame)
            for d in dets:
                detection_record = {
                    "plate_number": d["plate_number"],
                    "frame_number": frame_number,
                    "timestamp_seconds": timestamp_seconds,
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "detection_time": datetime.now().isoformat(),
                }
                detections.append(detection_record)
                
                # Write immediately to CSV and JSONL
                csv_writer.writerow({
                    "plate_number": detection_record["plate_number"],
                    "timestamp_seconds": detection_record["timestamp_seconds"],
                    "frame_number": detection_record["frame_number"],
                    "confidence": detection_record["confidence"],
                    "x1": detection_record["bbox"]["x1"],
                    "y1": detection_record["bbox"]["y1"],
                    "x2": detection_record["bbox"]["x2"],
                    "y2": detection_record["bbox"]["y2"],
                    "detection_time": detection_record["detection_time"],
                })
                csv_file.flush()  # Ensure data is written immediately
                
                json.dump(detection_record, jsonl_file)
                jsonl_file.write('\n')
                jsonl_file.flush()  # Ensure data is written immediately

            annotated = processor.annotate_frame(frame, dets)
            out.write(annotated)

            cv2.imshow("Webcam Plate Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("Stopping webcam capture (user pressed q).")
                break

    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        # Close incremental files
        if csv_file:
            csv_file.close()
        if jsonl_file:
            jsonl_file.close()
    
    # Create summary JSON file
    with open(json_path, "w") as f:
        json.dump(
            {
                "total_detections": len(detections),
                "unique_plates": len(set(d["plate_number"] for d in detections)),
                "detections": detections,
            },
            f,
            indent=2,
        )

    logger.info(
        "Finished. Frames: %s, total detections: %s, unique plates: %s",
        frame_number,
        len(detections),
        len(set(d["plate_number"] for d in detections)),
    )

    print("\n✓ Webcam run complete")
    print(f"Frames processed: {frame_number}")
    print(f"Total detections: {len(detections)}")
    print(f"Unique plates: {len(set(d['plate_number'] for d in detections))}")
    print(f"Output video: {output_video}")
    print(f"Detections JSON: {json_path}")
    print(f"Detections CSV: {csv_path}")


if __name__ == "__main__":
    main()

