# Parking Space Annotation Guide

## Quick Start

Run the annotation tool:
```bash
python3 annotate_spaces.py test_frame.jpg --output easy1_spaces_custom.json
```

## Step-by-Step Instructions

### 1. Launch the Tool
When you run the command, a window will open showing the video frame/image.

### 2. Draw Parking Spaces

For each parking space:

1. **Click** to place points around the parking space boundary
   - Start at one corner
   - Click around the perimeter (minimum 3 points, but 4+ recommended for rectangles)
   - You'll see a blue line connecting your points as you draw

2. **Press ENTER** when finished with the polygon
   - The space will turn green and show a space ID number
   - The next space will automatically start

3. **Repeat** for all parking spaces in the frame

### 3. Keyboard Controls

- **ENTER** or **RETURN**: Finish current polygon and save it
- **'d'** key: Delete the last completed space (if you made a mistake)
- **'s'** key: Save all spaces and exit
- **'q'** key: Quit without saving

### 4. Tips for Accurate Annotation

- **Draw tight boundaries**: Follow the actual parking space lines closely
- **Use 4 points for rectangles**: Most parking spaces are rectangular
- **Include the entire space**: Make sure the polygon covers the full parking spot
- **Avoid overlapping**: Don't let polygons overlap with each other
- **Start from corners**: Begin at a corner for easier alignment

### 5. Example Workflow

```
1. Click corner 1 of space 1
2. Click corner 2 of space 1
3. Click corner 3 of space 1
4. Click corner 4 of space 1
5. Press ENTER → Space #1 saved (green)
6. Click corner 1 of space 2
7. ... (repeat for all spaces)
8. Press 's' to save and exit
```

## Visual Feedback

- **Blue line**: Current polygon being drawn
- **Green filled polygon**: Completed parking space
- **White number**: Space ID (e.g., "#1", "#2")
- **Red outline**: Current polygon points

## After Annotation

Once you've saved your annotation file, run the analyzer:

```bash
python3 parking_analyzer.py --video easy1.mp4 --config easy1_spaces_custom.json --log easy1_changes.csv
```

## Troubleshooting

**Problem: Can't see the image clearly**
- The image might be too large - try zooming in your display
- The tool uses the full resolution of the image

**Problem: Accidentally clicked wrong point**
- Press 'd' to delete the last space and redraw it
- Or continue and fix it later by editing the JSON file

**Problem: Polygon looks wrong**
- You can delete it with 'd' and redraw
- Make sure you have at least 3 points

**Problem: Want to annotate a different frame**
- Extract a different frame: `python3 -c "import cv2; cap=cv2.VideoCapture('easy1.mp4'); cap.set(cv2.CAP_PROP_POS_FRAMES, 100); ret, f=cap.read(); cv2.imwrite('frame_100.jpg', f) if ret else None; cap.release()"`
- Then annotate that frame instead

## Editing Existing Annotations

You can manually edit the JSON file if needed:

```json
{
  "id": 1,
  "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
  "min_occupancy_ratio": 0.3
}
```

Coordinates are in pixels: `[x, y]` where:
- `x` = horizontal position (0 = left edge)
- `y` = vertical position (0 = top edge)

