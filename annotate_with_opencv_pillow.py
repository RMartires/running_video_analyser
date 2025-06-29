import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import mediapipe as mp
import math
from collections import Counter

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
    draw.rectangle([x - margin, y - margin, x + text_w  + margin, y + text_h + margin], fill=(30, 30, 30, 200))
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
    Draws a visually rich geometric angle overlay:
    - Two dashed arms (vertical and at angle)
    - Dashed or gradient arc connecting the arms (arc dashes follow the curve)
    - Transparent gradient wedge filling the angle
    - Angle value annotation
    All elements scale with image size.
    """
    draw = ImageDraw.Draw(img_pil, 'RGBA')
    x, y = center
    # Scale length and radius to image size
    img_w, img_h = img_pil.size
    length = int(min(img_w, img_h) * 0.13)
    arc_radius = int(length * 1.05)
    arc_width = max(2, int(length * 0.13))
    # Colors
    ARM_COLOR = (80, 255, 120, 220)  # Green, semi-transparent
    ARC_COLOR1 = (80, 255, 120, 200) # Green
    ARC_COLOR2 = (255, 255, 80, 200) # Yellow
    WEDGE_COLOR = (80, 255, 120, 90) # Green, more transparent
    # Geometry
    angle_rad = math.radians(angle_deg)
    # Arm endpoints
    vert_end = (x, y - length)
    torso_end = (x + length * math.sin(angle_rad), y - length * math.cos(angle_rad))
    # 1. Draw transparent gradient wedge
    steps = 40
    for i in range(steps):
        frac0 = i / steps
        frac1 = (i+1) / steps
        a0 = -math.pi/2 + angle_rad * frac0
        a1 = -math.pi/2 + angle_rad * frac1
        p0 = (x + arc_radius * math.cos(a0), y + arc_radius * math.sin(a0))
        p1 = (x + arc_radius * math.cos(a1), y + arc_radius * math.sin(a1))
        grad_alpha = int(WEDGE_COLOR[3] * (0.3 + 0.7 * frac1))
        color = (WEDGE_COLOR[0], WEDGE_COLOR[1], WEDGE_COLOR[2], grad_alpha)
        draw.polygon([center, p0, p1], fill=color)
    # 2. Draw dashed arms
    def draw_dashed(draw, p1, p2, color, width, dash=10, gap=7):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        dx, dy = dx / dist, dy / dist
        n = int(dist // (dash + gap)) + 1
        for i in range(n):
            start = i * (dash + gap)
            end = min(start + dash, dist)
            if start >= dist:
                break
            sx = p1[0] + dx * start
            sy = p1[1] + dy * start
            ex = p1[0] + dx * end
            ey = p1[1] + dy * end
            draw.line([(sx, sy), (ex, ey)], fill=color, width=width)
    draw_dashed(draw, center, vert_end, ARM_COLOR, arc_width)
    draw_dashed(draw, center, torso_end, ARM_COLOR, arc_width)
    # 3. Draw dashed/gradient arc (arc dashes follow the curve)
    def draw_dashed_arc(draw, center, radius, angle_start, angle_end, color1, color2, width, dash_angle_deg=12, gap_angle_deg=8):
        # Draw a dashed arc from angle_start to angle_end (radians), dashes follow the arc
        if abs(angle_end - angle_start) < 1e-4:
            return
        total_angle = angle_end - angle_start
        arc_len = abs(total_angle * radius)
        n = int(abs(math.degrees(total_angle)) // (dash_angle_deg + gap_angle_deg)) + 1
        for i in range(n):
            dash_a0 = angle_start + total_angle * (i * (dash_angle_deg + gap_angle_deg) / math.degrees(total_angle))
            dash_a1 = dash_a0 + math.radians(dash_angle_deg)
            if dash_a0 > angle_end:
                break
            dash_a1 = min(dash_a1, angle_end)
            # Gradient color for this dash
            t = (dash_a0 - angle_start) / (angle_end - angle_start) if angle_end != angle_start else 0
            arc_color = (
                int(color1[0] + (color2[0] - color1[0]) * t),
                int(color1[1] + (color2[1] - color1[1]) * t),
                int(color1[2] + (color2[2] - color1[2]) * t),
                int(color1[3] + (color2[3] - color1[3]) * t),
            )
            # Draw dash as many small segments along the arc
            segs = 8
            for j in range(segs):
                seg_a0 = dash_a0 + (dash_a1 - dash_a0) * (j / segs)
                seg_a1 = dash_a0 + (dash_a1 - dash_a0) * ((j+1) / segs)
                sx = center[0] + radius * math.cos(seg_a0)
                sy = center[1] + radius * math.sin(seg_a0)
                ex = center[0] + radius * math.cos(seg_a1)
                ey = center[1] + radius * math.sin(seg_a1)
                draw.line([(sx, sy), (ex, ey)], fill=arc_color, width=width)
    arc_angle_start = -math.pi/2
    arc_angle_end = -math.pi/2 + angle_rad
    draw_dashed_arc(draw, center, arc_radius, arc_angle_start, arc_angle_end, ARC_COLOR1, ARC_COLOR2, arc_width)
    # 4. Draw vertex circle
    draw.ellipse([x-arc_width, y-arc_width, x+arc_width, y+arc_width], fill=(255,255,255,180))
    # 5. Annotate angle value
    font_size = max(14, int(length * 0.35))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    label = f"{angle_deg:.1f}°"
    # Place label near arc midpoint
    mid_angle = arc_angle_start + (arc_angle_end - arc_angle_start) * 0.55
    lx = x + (arc_radius + arc_width*2) * math.cos(mid_angle)
    ly = y + (arc_radius + arc_width*2) * math.sin(mid_angle)
    draw.text((lx, ly), label, font=font, fill=(255,255,255,220))

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))

def draw_dashed_line(draw, p1, p2, color, width, dash_length=10, gap_length=8):
    # Draw a dashed line from p1 to p2
    x1, y1 = p1
    x2, y2 = p2
    total_len = math.hypot(x2 - x1, y2 - y1)
    if total_len == 0:
        return
    dx = (x2 - x1) / total_len
    dy = (y2 - y1) / total_len
    num_dashes = int(total_len // (dash_length + gap_length)) + 1
    for i in range(num_dashes):
        start = i * (dash_length + gap_length)
        end = min(start + dash_length, total_len)
        if start >= total_len:
            break
        sx = x1 + dx * start
        sy = y1 + dy * start
        ex = x1 + dx * end
        ey = y1 + dy * end
        draw.line([(sx, sy), (ex, ey)], fill=color, width=width)

def draw_gradient_line(draw, p1, p2, color1, color2, width, steps=16):
    # Draw a line from p1 to p2 with a gradient from color1 to color2
    x1, y1 = p1
    x2, y2 = p2
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        sx = x1 + (x2 - x1) * t0
        sy = y1 + (y2 - y1) * t0
        ex = x1 + (x2 - x1) * t1
        ey = y1 + (y2 - y1) * t1
        color = lerp_color(color1, color2, t0)
        draw.line([(sx, sy), (ex, ey)], fill=color, width=width)

def draw_pose_skeleton(img_pil, landmarks, width, height):
    """
    Draws a beautiful skeleton overlay with red (left), green (torso/head), blue (right),
    using thin, anti-aliased, dashed and gradient lines as in the mock.
    """
    draw = ImageDraw.Draw(img_pil, 'RGBA')
    # Color definitions (RGBA)
    RED1 = (255, 80, 80, 180)
    RED2 = (200, 0, 0, 180)
    BLUE1 = (80, 120, 255, 180)
    BLUE2 = (0, 0, 200, 180)
    GREEN1 = (80, 255, 120, 180)
    GREEN2 = (0, 200, 0, 180)
    # Line width scaling
    lw = max(1, int(min(width, height) * 0.008))
    joint_r = max(2, int(lw * 1.2))
    # Connections by part
    mp_pose = mp.solutions.pose
    # (start, end, color1, color2, style)
    SKELETON = [
        # Left arm (red, gradient, solid)
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_ELBOW.value, RED1, RED2, 'solid'),
        (mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_WRIST.value, RED2, RED1, 'solid'),
        # Right arm (blue, gradient, solid)
        (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value, BLUE1, BLUE2, 'solid'),
        (mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_WRIST.value, BLUE2, BLUE1, 'solid'),
        # Left leg (red, gradient, dashed)
        (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value, RED1, RED2, 'dashed'),
        (mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value, RED2, RED1, 'dashed'),
        # Right leg (blue, gradient, dashed)
        (mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value, BLUE1, BLUE2, 'dashed'),
        (mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value, BLUE2, BLUE1, 'dashed'),
        # Torso (green, solid)
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value, GREEN1, GREEN2, 'solid'),
        (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.RIGHT_HIP.value, GREEN2, GREEN1, 'solid'),
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_HIP.value, GREEN1, GREEN2, 'solid'),
        (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_HIP.value, GREEN2, GREEN1, 'solid'),
        # Head/neck (green, solid)
        (mp_pose.PoseLandmark.NOSE.value, mp_pose.PoseLandmark.LEFT_EYE.value, GREEN1, GREEN2, 'solid'),
        (mp_pose.PoseLandmark.NOSE.value, mp_pose.PoseLandmark.RIGHT_EYE.value, GREEN1, GREEN2, 'solid'),
        (mp_pose.PoseLandmark.LEFT_EYE.value, mp_pose.PoseLandmark.LEFT_EAR.value, GREEN2, GREEN1, 'solid'),
        (mp_pose.PoseLandmark.RIGHT_EYE.value, mp_pose.PoseLandmark.RIGHT_EAR.value, GREEN2, GREEN1, 'solid'),
        (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.NOSE.value, GREEN1, GREEN2, 'solid'),
        (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.NOSE.value, GREEN2, GREEN1, 'solid'),
    ]
    # Draw bones
    for start_idx, end_idx, c1, c2, style in SKELETON:
        p1 = landmarks[start_idx]
        p2 = landmarks[end_idx]
        xy1 = (int(p1.x * width), int(p1.y * height))
        xy2 = (int(p2.x * width), int(p2.y * height))
        if style == 'solid':
            draw_gradient_line(draw, xy1, xy2, c1, c2, lw)
        elif style == 'dashed':
            # Dashed with gradient: break into segments, alternate color
            steps = 12
            for i in range(steps):
                t0 = i / steps
                t1 = (i + 0.5) / steps
                if i % 2 == 0:
                    seg_c = lerp_color(c1, c2, t0)
                    sx = xy1[0] + (xy2[0] - xy1[0]) * t0
                    sy = xy1[1] + (xy2[1] - xy1[1]) * t0
                    ex = xy1[0] + (xy2[0] - xy1[0]) * t1
                    ey = xy1[1] + (xy2[1] - xy1[1]) * t1
                    draw.line([(sx, sy), (ex, ey)], fill=seg_c, width=lw)
    # Draw joints (small circles)
    joint_indices = set()
    for start_idx, end_idx, c1, c2, style in SKELETON:
        joint_indices.add(start_idx)
        joint_indices.add(end_idx)
    for idx in joint_indices:
        lm = landmarks[idx]
        x, y = int(lm.x * width), int(lm.y * height)
        # Color by part
        if idx in [mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_WRIST.value, mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value]:
            color = RED1
        elif idx in [mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_WRIST.value, mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value]:
            color = BLUE1
        else:
            color = GREEN1
        draw.ellipse([x-joint_r, y-joint_r, x+joint_r, y+joint_r], fill=color)

def annotate_video(input_path, output_path, font_path):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mp_pose = mp.solutions.pose
    # --- First pass: collect foot strike values ---
    foot_strike_list = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for frame_idx in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        metrics = get_metrics_for_frame(frame_idx)
        foot_strike_list.append(metrics['Foot Strike'])
    from collections import Counter
    foot_strike_mode = Counter(foot_strike_list).most_common(1)[0][0]
    # --- Second pass: annotate frames ---
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_idx = 0
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            metrics = get_metrics_for_frame(frame_idx)
            # Use per-frame metrics, but constant foot strike
            metrics['Foot Strike'] = foot_strike_mode
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
                draw_pose_skeleton(img_pil, landmarks, width, height)
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
                # draw_posture_angle_overlay(img_pil, angle_center, angle_deg=angle, length=60, alpha=128)
                frame_final = cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)
            else:
                # Fallback: no pose detected
                img_pil = Image.fromarray(cv2.cvtColor(frame_annotated, cv2.COLOR_BGR2RGB)).convert('RGBA')
                angle_center = (width // 2, int(height * 0.35))
                try:
                    angle = float(metrics.get('Posture Angle', 0))
                except Exception:
                    angle = 0
                # draw_posture_angle_overlay(img_pil, angle_center, angle_deg=angle, length=60, alpha=128)
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