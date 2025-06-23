import cv2
import mediapipe as mp
import numpy as np
import math
import sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

# --- Polished Drawing Helpers (Pillow for text/panels, OpenCV for overlays) ---
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Change if needed
FONT_SIZE_MAIN = 32
FONT_SIZE_SECONDARY = 26
PANEL_COLOR = (30, 30, 30, 200)  # RGBA
PANEL_RADIUS = 20
PANEL_PADDING = 16
PANEL_SPACING = 12


def draw_rounded_panel_pil(draw, xy, w, h, radius, fill):
    x, y = xy
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill)


def draw_metrics_panel(frame, metrics, top_left, font_main, font_secondary):
    # metrics: list of (label, value, color, is_main)
    # Convert frame to PIL RGBA
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    draw = ImageDraw.Draw(img_pil)
    # Calculate panel size
    max_label_w = 0
    max_value_w = 0
    total_h = PANEL_PADDING
    for label, value, color, is_main in metrics:
        font = font_main if is_main else font_secondary
        label_bbox = draw.textbbox((0,0), label, font=font)
        value_bbox = draw.textbbox((0,0), value, font=font)
        label_w, label_h = label_bbox[2] - label_bbox[0], label_bbox[3] - label_bbox[1]
        value_w, value_h = value_bbox[2] - value_bbox[0], value_bbox[3] - value_bbox[1]
        max_label_w = max(max_label_w, label_w)
        max_value_w = max(max_value_w, value_w)
        total_h += max(label_h, value_h) + PANEL_SPACING
    total_h += PANEL_PADDING - PANEL_SPACING
    panel_w = PANEL_PADDING + max_label_w + 16 + max_value_w + PANEL_PADDING
    panel_h = total_h
    # Draw rounded panel
    draw_rounded_panel_pil(draw, top_left, panel_w, panel_h, PANEL_RADIUS, PANEL_COLOR)
    # Draw metrics
    x, y = top_left[0] + PANEL_PADDING, top_left[1] + PANEL_PADDING
    for label, value, color, is_main in metrics:
        font = font_main if is_main else font_secondary
        # Draw label
        draw.text((x, y), label, font=font, fill=(220,220,220,255))
        # Draw value
        label_bbox = draw.textbbox((0,0), label, font=font)
        label_w, label_h = label_bbox[2] - label_bbox[0], label_bbox[3] - label_bbox[1]
        value_bbox = draw.textbbox((0,0), value, font=font)
        value_h = value_bbox[3] - value_bbox[1]
        draw.text((x + max_label_w + 16, y), value, font=font, fill=color)
        y += max(label_h, value_h) + PANEL_SPACING
    # Convert back to OpenCV BGR
    frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGBA2BGR)
    return frame


def draw_angle_overlay(frame, hip_mid, shoulder_mid, angle, color=(0,0,255)):
    h, w, _ = frame.shape
    hip_mid_px = (int(hip_mid[0] * w), int(hip_mid[1] * h))
    shoulder_mid_px = (int(shoulder_mid[0] * w), int(shoulder_mid[1] * h))
    cv2.line(frame, hip_mid_px, shoulder_mid_px, (255, 255, 255), 3)
    vert_end = (hip_mid_px[0], hip_mid_px[1] - 100)
    cv2.line(frame, hip_mid_px, vert_end, (0, 255, 0), 3)
    # Draw angle arc
    angle_radius = 50
    angle_start = math.atan2(shoulder_mid_px[1] - hip_mid_px[1], shoulder_mid_px[0] - hip_mid_px[0])
    angle_end = math.atan2(vert_end[1] - hip_mid_px[1], vert_end[0] - hip_mid_px[0])
    arc_pts = []
    for t in np.linspace(angle_end, angle_start, 20):
        x = int(hip_mid_px[0] + angle_radius * math.cos(t))
        y = int(hip_mid_px[1] + angle_radius * math.sin(t))
        arc_pts.append((x, y))
    for i in range(1, len(arc_pts)):
        cv2.line(frame, arc_pts[i-1], arc_pts[i], color, 3)
    # Annotate angle value
    cv2.putText(frame, f"{angle:.1f}°", (hip_mid_px[0]+60, hip_mid_px[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

# --- Analysis Functions (same as before, using mp_pose) ---
def calculate_torso_angle(landmarks):
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    hip_mid = ((left_hip.x + right_hip.x)/2, (left_hip.y + right_hip.y)/2)
    shoulder_mid = ((left_shoulder.x + right_shoulder.x)/2, (left_shoulder.y + right_shoulder.y)/2)
    dx = shoulder_mid[0] - hip_mid[0]
    dy = shoulder_mid[1] - hip_mid[1]
    return math.degrees(math.atan2(dx, -dy)), hip_mid, shoulder_mid

def classify_foot_strike(landmarks, foot):
    if foot == 'left':
        heel_idx = mp_pose.PoseLandmark.LEFT_HEEL
        toe_idx = mp_pose.PoseLandmark.LEFT_FOOT_INDEX
    else:
        heel_idx = mp_pose.PoseLandmark.RIGHT_HEEL
        toe_idx = mp_pose.PoseLandmark.RIGHT_FOOT_INDEX
    heel = landmarks[heel_idx.value]
    toe = landmarks[toe_idx.value]
    dx = toe.x - heel.x
    dy = toe.y - heel.y
    angle = math.degrees(math.atan2(dy, dx))
    if angle < -5:
        return 'heel'
    elif angle > 5:
        return 'forefoot'
    else:
        return 'midfoot'

def find_local_minima(y_coords, window=5):
    minima = []
    for i in range(window, len(y_coords) - window):
        if y_coords[i] is not None and all(y_coords[i] < y_coords[j] for j in range(i - window, i + window + 1) if j != i and y_coords[j] is not None):
            minima.append(i)
    return minima

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python annotate_analysis.py input_video.mp4 output_annotated.mp4")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening video file: {input_path}")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    mp_pose = mp.solutions.pose  # type: ignore
    font_main = ImageFont.truetype(FONT_PATH, FONT_SIZE_MAIN)
    font_secondary = ImageFont.truetype(FONT_PATH, FONT_SIZE_SECONDARY)
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        left_ankle_y = []
        right_ankle_y = []
        landmarks_list = []
        step_frames = []  # (frame_idx, 'left'/'right')
        strike_patterns = []
        torso_angles = []
        for frame_idx in range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))):
            ret, frame = cap.read()
            if not ret:
                break
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                landmarks_list.append(landmarks)
                left_ankle_y.append(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y)
                right_ankle_y.append(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y)
            else:
                landmarks_list.append(None)
                left_ankle_y.append(None)
                right_ankle_y.append(None)
        # Now, detect foot strikes for all frames
        left_strikes = find_local_minima(left_ankle_y)
        right_strikes = find_local_minima(right_ankle_y)
        for idx in left_strikes:
            step_frames.append((idx, 'left'))
        for idx in right_strikes:
            step_frames.append((idx, 'right'))
        step_frames.sort()
        # Precompute strike patterns
        for idx, foot in step_frames:
            if landmarks_list[idx]:
                strike_patterns.append(classify_foot_strike(landmarks_list[idx], foot))
        # Now, annotate per frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        step_count = 0
        strikes_so_far = []
        patterns_so_far = []
        for frame_idx in range(len(landmarks_list)):
            ret, frame = cap.read()
            if not ret:
                break
            # Step count logic
            while step_count < len(step_frames) and step_frames[step_count][0] <= frame_idx:
                strikes_so_far.append(step_frames[step_count])
                if landmarks_list[step_frames[step_count][0]]:
                    patterns_so_far.append(classify_foot_strike(landmarks_list[step_frames[step_count][0]], step_frames[step_count][1]))
                step_count += 1
            # Cadence logic
            elapsed_time = (frame_idx + 1) / fps
            current_steps = len(strikes_so_far)
            current_cadence = (current_steps * 60 / elapsed_time) if elapsed_time > 0 else 0
            # Predominant pattern
            if patterns_so_far:
                predominant_pattern = Counter(patterns_so_far).most_common(1)[0][0]
            else:
                predominant_pattern = 'unknown'
            # Posture angle
            angle, hip_mid, shoulder_mid = 0, (0,0), (0,0)
            if landmarks_list[frame_idx]:
                angle, hip_mid, shoulder_mid = calculate_torso_angle(landmarks_list[frame_idx])
                torso_angles.append(angle)
                # Draw angle overlay
                draw_angle_overlay(frame, hip_mid, shoulder_mid, angle)
            # Prepare metrics for panel
            metrics = [
                ("Step Count:", f"{current_steps}", (255,255,255,255), True),
                ("Cadence:", f"{current_cadence:.1f} spm", (255,255,0,255), True),
                ("Foot Strike:", f"{predominant_pattern}", (0,255,0,255), True),
                ("Frame:", f"{frame_idx+1}", (255,200,200,255), False),
            ]
            frame = draw_metrics_panel(frame, metrics, (20, 20), font_main, font_secondary)
            # Bottom panel for posture
            metrics2 = [
                ("Posture Angle:", f"{angle:.1f}°", (255,0,0,255), True),
            ]
            frame = draw_metrics_panel(frame, metrics2, (20, height-80), font_main, font_secondary)
            out.write(frame)
    cap.release()
    out.release()
    print(f"Polished annotated analysis video saved to {output_path}") 