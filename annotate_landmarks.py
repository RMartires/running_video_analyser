import cv2
import mediapipe as mp
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python annotate_landmarks.py input_video.mp4 output_annotated.mp4")
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
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    mp_pose = mp.solutions.pose  # type: ignore
    # Landmark info: (MediaPipe enum, display name, color (BGR))
    LANDMARKS = [
        (mp_pose.PoseLandmark.LEFT_ANKLE,        'Left Ankle',      (0, 0, 255)),    # Red
        (mp_pose.PoseLandmark.RIGHT_ANKLE,       'Right Ankle',     (0, 255, 255)),  # Yellow
        (mp_pose.PoseLandmark.LEFT_HEEL,         'Left Heel',       (255, 0, 0)),    # Blue
        (mp_pose.PoseLandmark.RIGHT_HEEL,        'Right Heel',      (255, 255, 0)),  # Cyan
        (mp_pose.PoseLandmark.LEFT_FOOT_INDEX,   'Left Toe',        (0, 255, 0)),    # Green
        (mp_pose.PoseLandmark.RIGHT_FOOT_INDEX,  'Right Toe',       (255, 0, 255)),  # Magenta
        (mp_pose.PoseLandmark.LEFT_HIP,          'Left Hip',        (128, 0, 128)),  # Purple
        (mp_pose.PoseLandmark.RIGHT_HIP,         'Right Hip',       (0, 128, 128)),  # Teal
        (mp_pose.PoseLandmark.LEFT_SHOULDER,     'Left Shoulder',   (0, 128, 255)),  # Orange
        (mp_pose.PoseLandmark.RIGHT_SHOULDER,    'Right Shoulder',  (128, 255, 0)),  # Light Green
    ]
    with mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)
            if results.pose_landmarks:
                h, w, _ = frame.shape
                for landmark_enum, label, color in LANDMARKS:
                    lm = results.pose_landmarks.landmark[landmark_enum.value]
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 8, color, -1)
                    cv2.putText(frame, label, (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
                # Optionally, draw lines for posture (hip to shoulder)
                left_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value]
                right_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP.value]
                left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                hip_mid = (int((left_hip.x + right_hip.x)/2 * w), int((left_hip.y + right_hip.y)/2 * h))
                shoulder_mid = (int((left_shoulder.x + right_shoulder.x)/2 * w), int((left_shoulder.y + right_shoulder.y)/2 * h))
                cv2.line(frame, hip_mid, shoulder_mid, (255, 255, 255), 2)
            out.write(frame)
            frame_idx += 1
    cap.release()
    out.release()
    print(f"Annotated video saved to {output_path}") 