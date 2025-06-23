import cv2
import mediapipe as mp
import numpy as np
import math

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose  # type: ignore

def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Error opening video file")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames, fps, duration

def detect_landmarks(frames):
    landmarks_list = []
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for frame in frames:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            landmarks_list.append(results.pose_landmarks.landmark if results.pose_landmarks else None)
    return landmarks_list

def extract_ankle_positions(landmarks_list):
    left_ankle_y = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y if landmarks else None for landmarks in landmarks_list]
    right_ankle_y = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y if landmarks else None for landmarks in landmarks_list]
    return left_ankle_y, right_ankle_y

def find_local_minima(y_coords, window=5):
    minima = []
    for i in range(window, len(y_coords) - window):
        if y_coords[i] is not None and all(y_coords[i] < y_coords[j] for j in range(i - window, i + window + 1) if j != i and y_coords[j] is not None):
            minima.append(i)
    return minima

def detect_foot_strikes(left_ankle_y, right_ankle_y):
    left_strikes = find_local_minima(left_ankle_y)
    right_strikes = find_local_minima(right_ankle_y)
    return left_strikes, right_strikes

def calculate_cadence(left_strikes, right_strikes, duration):
    total_strikes = len(left_strikes) + len(right_strikes)
    return total_strikes * 60 / duration if duration > 0 else 0

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
    dy = toe.y - heel.y  # y increases downward
    angle = math.degrees(math.atan2(dy, dx))
    if angle < -5:
        return 'heel'
    elif angle > 5:
        return 'forefoot'
    else:
        return 'midfoot'

def calculate_torso_angle(landmarks):
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    hip_mid = ((left_hip.x + right_hip.x)/2, (left_hip.y + right_hip.y)/2)
    shoulder_mid = ((left_shoulder.x + right_shoulder.x)/2, (left_shoulder.y + right_shoulder.y)/2)
    dx = shoulder_mid[0] - hip_mid[0]
    dy = shoulder_mid[1] - hip_mid[1]
    return math.degrees(math.atan2(dx, -dy))  # angle from vertical

def generate_report(cadence, foot_strike_pattern, posture, posture_percentages, total_strikes, duration):
    return f"""
Running Form Analysis:
- Video Duration: {duration:.2f} seconds
- Total Foot Strikes: {total_strikes}
- Cadence: {cadence:.2f} steps per minute
- Predominant Foot Strike Pattern: {foot_strike_pattern}
- Posture: {posture}
  - Good: {posture_percentages['good']:.1f}%
  - Excessive Forward Lean: {posture_percentages['excessive forward lean']:.1f}%
  - Leaning Back: {posture_percentages['leaning back']:.1f}%
"""

def processRunningVideo(video_path):
    # Step 1: Read the video
    frames, fps, duration = read_video(video_path)
    # Step 2: Detect landmarks
    landmarks_list = detect_landmarks(frames)
    # Filter valid frames
    valid_indices = [i for i, landmarks in enumerate(landmarks_list) if landmarks is not None]
    if len(valid_indices) < 10:
        raise ValueError("Insufficient valid frames for analysis")
    # Step 3: Analyze foot strikes
    left_ankle_y, right_ankle_y = extract_ankle_positions(landmarks_list)
    left_strikes, right_strikes = detect_foot_strikes(left_ankle_y, right_ankle_y)
    left_strikes = [valid_indices[i] for i in left_strikes if i < len(valid_indices)]
    right_strikes = [valid_indices[i] for i in right_strikes if i < len(valid_indices)]
    total_strikes = len(left_strikes) + len(right_strikes)

    # Step 4: Calculate cadence
    cadence = calculate_cadence(left_strikes, right_strikes, duration)
    # Step 5: Determine foot strike pattern
    strike_patterns = []
    for foot, frame_idx in [('left', idx) for idx in left_strikes] + [('right', idx) for idx in right_strikes]:
        pattern = classify_foot_strike(landmarks_list[frame_idx], foot)
        strike_patterns.append(pattern)
    predominant_pattern = max(set(strike_patterns), key=strike_patterns.count) if strike_patterns else 'unknown'
    # Step 6: Assess posture
    torso_angles = [calculate_torso_angle(landmarks_list[i]) for i in valid_indices]
    posture_counts = {'good': 0, 'excessive forward lean': 0, 'leaning back': 0}
    for angle in torso_angles:
        if -5 <= angle <= 10:
            posture_counts['good'] += 1
        elif angle > 10:
            posture_counts['excessive forward lean'] += 1
        else:
            posture_counts['leaning back'] += 1
    total_posture = sum(posture_counts.values())
    posture_percentages = {k: (v / total_posture * 100) if total_posture > 0 else 0 for k, v in posture_counts.items()}
    average_angle = np.mean(torso_angles) if torso_angles else 0
    if -5 <= average_angle <= 10:
        posture = 'good'
    elif average_angle > 10:
        posture = 'excessive forward lean'
    else:
        posture = 'leaning back'
    # Step 7: Generate report
    report = generate_report(cadence, predominant_pattern, posture, posture_percentages, total_strikes, duration)
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python running_analysis.py <video_path>")
    else:
        video_path = sys.argv[1]
        try:
            result = processRunningVideo(video_path)
            print(result)
        except Exception as e:
            print(f"Error: {e}") 