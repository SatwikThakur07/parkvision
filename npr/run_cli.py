"""CLI interface for video processing"""
import argparse
import sys
from pathlib import Path
from src.video_processor import VideoProcessor
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.log_level, settings.log_dir)


def main():
    parser = argparse.ArgumentParser(description="License Plate Detection CLI")
    parser.add_argument("input_video", help="Path to input video file")
    parser.add_argument("-o", "--output", help="Path to output video file")
    parser.add_argument("--no-detections", action="store_true", help="Don't save detection files")
    parser.add_argument("--preview", action="store_true", help="Show preview window")
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_video)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        processor = VideoProcessor()
        result = processor.process_video(
            str(input_path),
            output_path=args.output,
            save_detections=not args.no_detections,
            show_preview=args.preview
        )
        
        print("\n" + "="*50)
        print("Processing Complete!")
        print("="*50)
        print(f"Input: {result['input_video']}")
        print(f"Output: {result['output_video']}")
        print(f"Total Frames: {result['total_frames']}")
        print(f"Total Detections: {result['total_detections']}")
        print(f"Unique Plates: {result['unique_plates']}")
        if result.get('detection_files'):
            print(f"Detection Files:")
            print(f"  JSON: {result['detection_files']['json']}")
            print(f"  CSV: {result['detection_files']['csv']}")
        print("="*50)
    
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

