import cv2
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, VideoClip
import numpy as np
import mediapipe as mp
import math
from PIL import ImageFont


font = ImageFont.load_default()
print(font)

# --- Helper functions for metrics (reuse logic from running_analysis.py) ---
def calculate_torso_angle(landmarks):
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    hip_mid = ((left_hip.x + right_hip.x)/2, (left_hip.y + right_hip.y)/2)
    shoulder_mid = ((left_shoulder.x + right_shoulder.x)/2, (left_shoulder.y + right_shoulder.y)/2)
    dx = shoulder_mid[0] - hip_mid[0]
    dy = shoulder_mid[1] - hip_mid[1]
    return math.degrees(math.atan2(dx, -dy))

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

def make_text_frame(t):
    idx = min(int(t * fps), len(step_count_per_frame) - 1)
    txt = (f"Step Count: {step_count_per_frame[idx]}\n"
            f"Cadence: {cadence_per_frame[idx]:.1f} spm\n"
            f"Foot Strike: {pattern_per_frame[idx]}\n"
            f"Posture Angle: {angle_per_frame[idx]:.1f}°")
    txt_clip = TextClip(
        txt,
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        font_size=fontsize,
        color='white',
        bg_color='rgba(30,30,30,0.7)',
        method='label',
        size=(int(width*0.15), None)
    )
    return txt_clip.get_frame(t)


if __name__ == "__main__":
    import sys
    from collections import Counter
    if len(sys.argv) != 3:
        print("Usage: python annotate_analysis_moviepy.py input_video.mp4 output_annotated.mp4")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Step 1: Analyze video with mediapipe to get metrics per frame
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    mp_pose = mp.solutions.pose  # type: ignore
    left_ankle_y = []
    right_ankle_y = []
    landmarks_list = []
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for _ in range(frame_count):
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
    cap.release()
    # Detect foot strikes
    left_strikes = find_local_minima(left_ankle_y)
    right_strikes = find_local_minima(right_ankle_y)
    step_frames = []
    for idx in left_strikes:
        step_frames.append((idx, 'left'))
    for idx in right_strikes:
        step_frames.append((idx, 'right'))
    step_frames.sort()
    # Precompute metrics per frame
    step_count_per_frame = []
    cadence_per_frame = []
    pattern_per_frame = []
    angle_per_frame = []
    strikes_so_far = []
    patterns_so_far = []
    for frame_idx in range(len(landmarks_list)):
        # Step count
        while strikes_so_far and strikes_so_far[0][0] < frame_idx:
            strikes_so_far.pop(0)
        while len(strikes_so_far) < len(step_frames) and step_frames[len(strikes_so_far)][0] <= frame_idx:
            strikes_so_far.append(step_frames[len(strikes_so_far)])
            if landmarks_list[step_frames[len(strikes_so_far)-1][0]]:
                patterns_so_far.append(classify_foot_strike(landmarks_list[step_frames[len(strikes_so_far)-1][0]], step_frames[len(strikes_so_far)-1][1]))
        step_count = len([s for s in strikes_so_far if s[0] <= frame_idx])
        step_count_per_frame.append(step_count)
        # Cadence
        elapsed_time = (frame_idx + 1) / fps
        cadence = (step_count * 60 / elapsed_time) if elapsed_time > 0 else 0
        cadence_per_frame.append(cadence)
        # Pattern
        if patterns_so_far:
            predominant_pattern = Counter(patterns_so_far).most_common(1)[0][0]
        else:
            predominant_pattern = 'unknown'
        pattern_per_frame.append(predominant_pattern)
        # Angle
        if landmarks_list[frame_idx]:
            angle = calculate_torso_angle(landmarks_list[frame_idx])
        else:
            angle = 0
        angle_per_frame.append(angle)

    # Step 2: Create MoviePy VideoClip with dynamic metrics as text panel
    video_clip = VideoFileClip(input_path)
    fontsize = max(12, int(height * 0.045))
    dynamic_text_clip = VideoClip(make_text_frame, duration=video_clip.duration).pos((20, 20))
    # Step 3: Composite and export
    final = CompositeVideoClip([video_clip, dynamic_text_clip])
    final.write_videofile(output_path, codec='libx264', audio_codec='aac') 

