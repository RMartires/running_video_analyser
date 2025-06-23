import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# Example metrics for demonstration (replace with your own logic)
def get_metrics_for_frame(frame_idx):
    return {
        'Step Count': frame_idx // 10,
        'Cadence': 180 + (frame_idx % 10),
        'Foot Strike': 'heel' if frame_idx % 2 == 0 else 'forefoot',
        'Posture Angle': -5.0 + (frame_idx % 15)
    }

def draw_text_panel(frame, metrics, font_path, font_size=32, panel_pos=(20, 20)):
    # Convert frame to PIL image
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    # Prepare text
    lines = [f"{k}: {v}" for k, v in metrics.items()]
    text = "\n".join(lines)
    # Calculate text size
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Draw background rectangle
    margin = 10
    x, y = panel_pos
    draw.rectangle([x - margin, y - margin, x + text_w + margin, y + text_h + margin], fill=(30, 30, 30, 200))
    # Draw text
    draw.multiline_text((x, y), text, font=font, fill=(255, 255, 255, 255))
    # Convert back to OpenCV
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

def annotate_video(input_path, output_path, font_path):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    # FourCC code for mp4
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        metrics = get_metrics_for_frame(frame_idx)
        frame_annotated = draw_text_panel(frame, metrics, font_path, font_size=max(16, int(height * 0.045)))
        out.write(frame_annotated)
        frame_idx += 1
    cap.release()
    out.release()
    print(f"Annotated video saved to {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python annotate_with_opencv_pillow.py input_video.mp4 output_annotated.mp4")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    # Use a system font for demonstration
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        print(f"Font file not found: {font_path}")
        sys.exit(1)
    annotate_video(input_path, output_path, font_path) 