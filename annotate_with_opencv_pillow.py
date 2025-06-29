import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import mediapipe as mp

# Example metrics for demonstration (replace with your own logic)
def get_metrics_for_frame(frame_idx):
    return {
        'Step Count': frame_idx // 10,
        'Cadence': 180 + (frame_idx % 10),
        'Foot Strike': 'heel' if frame_idx % 2 == 0 else 'forefoot',
        'Posture Angle': -5.0 + (frame_idx % 15)
    }

def draw_gradient_triangle(img_pil, base_center, angle_deg, size, alpha=128):
    """
    Draw a semi-transparent, gradient green triangle representing the posture angle.
    base_center: (x, y) center of the triangle base
    angle_deg: angle in degrees (0 is up)
    size: length of triangle sides
    alpha: transparency (0-255)
    """
    import math
    x, y = base_center
    angle_rad = math.radians(angle_deg)
    # Triangle points: tip and two base corners
    tip = (x, y - size)
    base_left = (x - size // 2, y)
    base_right = (x + size // 2, y)
    # Rotate points around base_center by angle_rad
    def rotate(px, py):
        dx, dy = px - x, py - y
        rx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        ry = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        return (x + rx, y + ry)
    tip = rotate(*tip)
    base_left = rotate(*base_left)
    base_right = rotate(*base_right)
    # Create a mask for gradient
    triangle_img = Image.new('RGBA', img_pil.size, (0,0,0,0))
    triangle_draw = ImageDraw.Draw(triangle_img)
    # Draw gradient by interpolating green color from base to tip
    steps = 50
    for i in range(steps):
        frac = i / steps
        # Interpolate between base and tip
        p1 = (
            base_left[0] * (1 - frac) + tip[0] * frac,
            base_left[1] * (1 - frac) + tip[1] * frac
        )
        p2 = (
            base_right[0] * (1 - frac) + tip[0] * frac,
            base_right[1] * (1 - frac) + tip[1] * frac
        )
        color = (int(50 + 100*frac), int(200 + 55*frac), int(50 + 100*frac), alpha)
        triangle_draw.polygon([base_left, base_right, p2, p1], fill=color)
        base_left, base_right = p1, p2
    # Composite the triangle onto the main image
    img_pil.alpha_composite(triangle_img)

def draw_gradient_angle(img_pil, center, angle_deg, radius=40, width=12, alpha=128):
    """
    Draw a semi-transparent, gradient green angle (arc) representing the posture angle.
    center: (x, y) center of the arc
    angle_deg: posture angle in degrees (0 is up)
    radius: radius of the arc
    width: thickness of the arc
    alpha: transparency (0-255)
    """
    import math
    from PIL import ImageDraw
    arc_img = Image.new('RGBA', img_pil.size, (0,0,0,0))
    arc_draw = ImageDraw.Draw(arc_img)
    x, y = center
    # Arc starts at -90 (vertical up), sweeps to angle_deg
    start_angle = -90
    end_angle = -90 + angle_deg
    steps = max(10, int(abs(angle_deg)))
    for i in range(steps):
        frac = i / steps
        color = (int(50 + 100*frac), int(200 + 55*frac), int(50 + 100*frac), alpha)
        # Interpolate angle for gradient
        a0 = start_angle + (end_angle - start_angle) * frac
        a1 = start_angle + (end_angle - start_angle) * (frac + 1/steps)
        arc_draw.arc([
            x - radius, y - radius, x + radius, y + radius
        ], start=a0, end=a1, fill=color, width=width)
    img_pil.alpha_composite(arc_img)

def draw_text_panel(frame, metrics, font_path, font_size=32, panel_pos=(20, 20), draw_arc=True):
    # Convert frame to PIL image
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert('RGBA')
    draw = ImageDraw.Draw(img_pil, 'RGBA')
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
    # Optionally draw arc (for backward compatibility, not used in main loop)
    if draw_arc:
        try:
            angle = float(metrics.get('Posture Angle', 0))
        except Exception:
            angle = 0
        arc_center = (x + text_w // 2, y + text_h + margin + 40)
        draw_gradient_angle(img_pil, arc_center, angle_deg=angle, radius=40, width=12, alpha=128)
    # Convert back to OpenCV
    return cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)

def draw_posture_angle_overlay(img_pil, center, angle_deg, length=60, alpha=128):
    """
    Draws a visually appealing geometric angle overlay:
    - Vertical line: semi-transparent white
    - Torso line: vibrant green
    - Wedge: soft radial gradient from transparent to green
    - Vertex: small semi-transparent white circle
    center: (x, y) vertex of the angle (hip midpoint in overlay)
    angle_deg: posture angle in degrees (0 is up, positive is clockwise)
    length: length of the lines
    alpha: transparency (0-255)
    """
    import math
    overlay = Image.new('RGBA', img_pil.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    x, y = center
    # Vertical line (up)
    vert_end = (x, y - length)
    # Torso line (rotated by angle_deg from vertical, clockwise)
    angle_rad = math.radians(angle_deg)
    torso_end = (x + length * math.sin(angle_rad), y - length * math.cos(angle_rad))
    # Draw wedge (soft radial gradient)
    steps = 60
    for i in range(steps):
        frac0 = i / steps
        frac1 = (i+1) / steps
        a0 = -math.pi/2 + angle_rad * frac0
        a1 = -math.pi/2 + angle_rad * frac1
        p0 = (x + length * 0.95 * math.cos(a0 + math.pi/2), y + length * 0.95 * math.sin(a0 + math.pi/2))
        p1 = (x + length * 0.95 * math.cos(a1 + math.pi/2), y + length * 0.95 * math.sin(a1 + math.pi/2))
        # Gradient: more transparent near the vertex, more green at the edge
        grad_alpha = int(alpha * (0.3 + 0.7 * frac1))
        color = (60, 255, 100, grad_alpha)
        draw.polygon([center, p0, p1], fill=color)
    # Draw vertical line (white, semi-transparent, thick)
    draw.line([center, vert_end], fill=(255,255,255,180), width=7)
    # Draw torso line (vibrant green, semi-transparent, thick)
    draw.line([center, torso_end], fill=(60,255,100,220), width=7)
    # Draw vertex circle (white, semi-transparent)
    draw.ellipse([x-7, y-7, x+7, y+7], fill=(255,255,255,180))
    img_pil.alpha_composite(overlay)

def draw_pose_skeleton(img_pil, landmarks, width, height, connections, joint_color=(0,255,0,180), bone_color=(255,255,255,180)):
    """
    Draws the pose skeleton on a PIL image using the given landmarks and connections.
    - landmarks: list of pose landmarks (normalized)
    - width, height: image dimensions
    - connections: list of (start_idx, end_idx) tuples
    - joint_color: RGBA color for joints
    - bone_color: RGBA color for bones
    """
    draw = ImageDraw.Draw(img_pil, 'RGBA')
    # Draw bones
    for start_idx, end_idx in connections:
        p1 = landmarks[start_idx]
        p2 = landmarks[end_idx]
        x1, y1 = int(p1.x * width), int(p1.y * height)
        x2, y2 = int(p2.x * width), int(p2.y * height)
        draw.line([(x1, y1), (x2, y2)], fill=bone_color, width=5)
    # Draw joints
    for lm in landmarks:
        x, y = int(lm.x * width), int(lm.y * height)
        draw.ellipse([x-6, y-6, x+6, y+6], fill=joint_color)

def annotate_video(input_path, output_path, font_path):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    frame_idx = 0
    mp_pose = mp.solutions.pose
    # MediaPipe pose connections (subset for clarity)
    POSE_CONNECTIONS = [
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value),
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_ELBOW.value),
        (mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_WRIST.value),
        (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value),
        (mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_WRIST.value),
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_HIP.value),
        (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_HIP.value),
        (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.RIGHT_HIP.value),
        (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value),
        (mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value),
        (mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value),
        (mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value),
    ]
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            metrics = get_metrics_for_frame(frame_idx)
            # Draw text panel as before
            frame_annotated = draw_text_panel(frame, metrics, font_path, font_size=max(16, int(height * 0.045)), draw_arc=False)
            # Extract pose landmarks for this frame
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                # Convert to PIL for overlay
                img_pil = Image.fromarray(cv2.cvtColor(frame_annotated, cv2.COLOR_BGR2RGB)).convert('RGBA')
                # Draw skeleton
                draw_pose_skeleton(img_pil, landmarks, width, height, POSE_CONNECTIONS)
                # Calculate hip midpoint for posture angle overlay
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                hip_mid_x = int((left_hip.x + right_hip.x) / 2 * width)
                hip_mid_y = int((left_hip.y + right_hip.y) / 2 * height)
                angle_center = (hip_mid_x, hip_mid_y)
                try:
                    angle = float(metrics.get('Posture Angle', 0))
                except Exception:
                    angle = 0
                draw_posture_angle_overlay(img_pil, angle_center, angle_deg=angle, length=60, alpha=128)
                frame_final = cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)
            else:
                # Fallback: no pose detected
                img_pil = Image.fromarray(cv2.cvtColor(frame_annotated, cv2.COLOR_BGR2RGB)).convert('RGBA')
                angle_center = (width // 2, int(height * 0.35))
                try:
                    angle = float(metrics.get('Posture Angle', 0))
                except Exception:
                    angle = 0
                draw_posture_angle_overlay(img_pil, angle_center, angle_deg=angle, length=60, alpha=128)
                frame_final = cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)
            out.write(frame_final)
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