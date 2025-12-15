# Reusing Parking Space Annotations

## ✅ Good News: Annotations Are Saved!

When you annotate parking spaces, they are automatically saved to a JSON file (e.g., `easy1_spaces.json`). **You can reuse this file for any video from the same camera setup!**

## When You Can Reuse Annotations

✅ **Same camera position/angle** - Reuse the config file  
✅ **Same video resolution** - Reuse the config file  
✅ **Different videos, same parking lot** - Reuse the config file  
✅ **Different times of day** - Reuse the config file  

## When You Need to Re-annotate

❌ **Different camera position** - Need new annotations  
❌ **Different video resolution** - Need to scale or re-annotate  
❌ **Different parking lot** - Need new annotations  
❌ **Camera moved/rotated** - Need new annotations  

## How to Reuse Saved Annotations

### Example 1: Same Parking Lot, Different Video

```bash
# You already have: easy1_spaces.json

# Use it with a different video:
python3 parking_analyzer.py --video another_video.mp4 --config easy1_spaces.json

# Or with webcam (same camera):
python3 parking_analyzer.py --webcam 0 --config easy1_spaces.json

# Or with RTSP stream (same camera):
python3 parking_analyzer.py --rtsp rtsp://... --config easy1_spaces.json
```

### Example 2: Organize Multiple Parking Lots

```bash
# Parking lot A
python3 annotate_spaces.py lot_a_frame.jpg --output lot_a_spaces.json
python3 parking_analyzer.py --video lot_a_video1.mp4 --config lot_a_spaces.json
python3 parking_analyzer.py --video lot_a_video2.mp4 --config lot_a_spaces.json

# Parking lot B (different location)
python3 annotate_spaces.py lot_b_frame.jpg --output lot_b_spaces.json
python3 parking_analyzer.py --video lot_b_video1.mp4 --config lot_b_spaces.json
```

## Checking Your Saved Annotations

View your saved spaces:
```bash
python3 -c "import json; d=json.load(open('easy1_spaces.json')); print(f'Spaces: {len(d[\"spaces\"])}')"
```

## Handling Different Resolutions

If you have videos with different resolutions but same camera angle:

### Option 1: Scale the coordinates (if aspect ratio is same)
You can write a script to scale the coordinates proportionally.

### Option 2: Re-annotate (recommended)
Extract a frame from the new video and annotate it:
```bash
python3 -c "import cv2; cap=cv2.VideoCapture('new_video.mp4'); ret, f=cap.read(); cv2.imwrite('new_frame.jpg', f) if ret else None; cap.release()"
python3 annotate_spaces.py new_frame.jpg --output new_video_spaces.json
```

## Best Practices

1. **Name your config files descriptively:**
   - `parking_lot_entrance_spaces.json`
   - `parking_lot_exit_spaces.json`
   - `camera_1_spaces.json`

2. **Keep config files organized:**
   ```
   configs/
     ├── lot_a_entrance.json
     ├── lot_a_exit.json
     └── lot_b_main.json
   ```

3. **Document your configs:**
   Add a comment in the JSON or keep a README noting:
   - Camera location
   - Video resolution
   - Date annotated
   - Number of spaces

## Your Current Setup

You have: `easy1_spaces.json` with 20 spaces

Use it for any video from the same camera:
```bash
python3 parking_analyzer.py --video any_video.mp4 --config easy1_spaces.json
```

