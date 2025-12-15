"""Video processing module"""
import cv2
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from src.plate_processor import PlateProcessor
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.log_level, settings.log_dir)


class VideoProcessor:
    """Process video files for license plate detection"""
    
    def __init__(self):
        """Initialize video processor"""
        self.processor = PlateProcessor()
    
    def process_video(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        save_detections: bool = True,
        show_preview: bool = False
    ) -> Dict:
        """Process video and detect license plates"""
        logger.info(f"Processing video: {input_path}")
        
        if output_path is None:
            output_path = str(Path(settings.output_dir) / f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties: {width}x{height}, {fps} FPS, {total_frames} frames")
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        detected_plates = []
        frame_number = 0
        
        # Initialize incremental file writing if save_detections is enabled
        csv_file = None
        csv_writer = None
        json_file = None
        csv_path = None
        jsonl_path = None
        if save_detections:
            file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.csv"
            jsonl_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.jsonl"  # JSONL for streaming
            
            # Open CSV file for writing
            csv_file = open(csv_path, 'w', newline='')
            csv_writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "plate_number", "frame_number", "timestamp_seconds",
                    "confidence", "x1", "y1", "x2", "y2", "detection_time"
                ]
            )
            csv_writer.writeheader()
            
            # Open JSONL file for streaming JSON
            json_file = open(jsonl_path, 'w')
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number += 1
                timestamp = frame_number / fps if fps > 0 else 0
                
                # Detect plates
                detections = self.processor.detect_plates(frame)
                
                # Store detections and write immediately
                for detection in detections:
                    detection_record = {
                        "plate_number": detection["plate_number"],
                        "frame_number": frame_number,
                        "timestamp_seconds": round(timestamp, 2),
                        "confidence": detection["confidence"],
                        "bbox": detection["bbox"],
                        "detection_time": datetime.now().isoformat()
                    }
                    detected_plates.append(detection_record)
                    
                    # Write immediately to CSV and JSONL if enabled
                    if csv_writer:
                        csv_writer.writerow({
                            "plate_number": detection_record["plate_number"],
                            "frame_number": detection_record["frame_number"],
                            "timestamp_seconds": detection_record["timestamp_seconds"],
                            "confidence": detection_record["confidence"],
                            "x1": detection_record["bbox"]["x1"],
                            "y1": detection_record["bbox"]["y1"],
                            "x2": detection_record["bbox"]["x2"],
                            "y2": detection_record["bbox"]["y2"],
                            "detection_time": detection_record["detection_time"]
                        })
                        csv_file.flush()  # Ensure data is written immediately
                    
                    if json_file:
                        json.dump(detection_record, json_file)
                        json_file.write('\n')
                        json_file.flush()  # Ensure data is written immediately
                
                # Annotate frame
                annotated_frame = self.processor.annotate_frame(frame, detections)
                
                # Write frame
                out.write(annotated_frame)
                
                # Show preview if requested
                if show_preview:
                    cv2.imshow("Annotated Video", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("Processing interrupted by user")
                        break
                
                # Log progress
                if frame_number % 100 == 0:
                    logger.info(f"Processed {frame_number}/{total_frames} frames")
        
        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            raise
        
        finally:
            cap.release()
            out.release()
            if show_preview:
                cv2.destroyAllWindows()
            
            # Close incremental files
            if csv_file:
                csv_file.close()
            if json_file:
                json_file.close()
        
        # Save detections summary (JSON format) if requested
        detection_files = {}
        if save_detections and detected_plates:
            # CSV and JSONL already saved incrementally, now create summary JSON
            if csv_path:
                file_timestamp = csv_path.stem.replace('detected_plates_', '')
                json_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.json"
            else:
                file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                json_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.json"
                jsonl_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.jsonl"
                csv_path = Path(settings.output_dir) / f"detected_plates_{file_timestamp}.csv"
            
            # Create summary JSON file
            with open(json_path, 'w') as f:
                json.dump({
                    "total_detections": len(detected_plates),
                    "unique_plates": len(set(plate["plate_number"] for plate in detected_plates)),
                    "detections": detected_plates
                }, f, indent=2)
            
            detection_files = {
                "json": str(json_path),
                "jsonl": str(jsonl_path),  # Streaming JSON Lines format
                "csv": str(csv_path)
            }
            
            logger.info(f"Saved detections: {len(detected_plates)} detections, {len(set(plate['plate_number'] for plate in detected_plates))} unique plates")
        
        unique_plates = len(set(plate["plate_number"] for plate in detected_plates))
        
        result = {
            "input_video": input_path,
            "output_video": output_path,
            "total_frames": frame_number,
            "total_detections": len(detected_plates),
            "unique_plates": unique_plates,
            "detection_files": detection_files
        }
        
        logger.info(f"Processing complete: {len(detected_plates)} detections, {unique_plates} unique plates")
        
        return result
    
    def _save_detections(self, detected_plates: List[Dict]) -> Dict[str, str]:
        """Save detections to JSON and CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_path = Path(settings.output_dir) / f"detected_plates_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                "total_detections": len(detected_plates),
                "unique_plates": len(set(plate["plate_number"] for plate in detected_plates)),
                "detections": detected_plates
            }, f, indent=2)
        
        # Save CSV
        csv_path = Path(settings.output_dir) / f"detected_plates_{timestamp}.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "plate_number", "frame_number", "timestamp_seconds",
                    "confidence", "x1", "y1", "x2", "y2", "detection_time"
                ]
            )
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
        
        logger.info(f"Saved detections to {json_path} and {csv_path}")
        
        return {
            "json": str(json_path),
            "csv": str(csv_path)
        }

