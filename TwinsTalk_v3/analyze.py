import os
import cv2
import json
import mediapipe as mp
import subprocess

# ffmpeg 轉碼為 HTML5 可播放 H.264 影片
def convert_to_h264(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264',
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print("❌ ffmpeg 轉碼失敗")
        print(result.stderr.decode())
    else:
        print(f"✅ 已轉檔為 H.264：{output_path}")
        os.remove(input_path)


def analyze_pose(video_path, output_json_path, output_video_path):
    print(f"🔍 [Pose] 分析影片：{video_path}")

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    results_all = []

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    raw_output_video_path = output_video_path.replace('.mp4', '_raw.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_output_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        landmark_list = []
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )
            for lm in results.pose_landmarks.landmark:
                landmark_list.append({
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility
                })

        results_all.append({
            'frame': frame_count,
            'landmarks': landmark_list
        })

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results_all, f, indent=2)

    # 轉為 H.264 + faststart
    convert_to_h264(raw_output_video_path, output_video_path)


def analyze_object_detection(video_path, output_json_path, output_video_path):
    print(f"🔍 [Object Detection] 分析影片：{video_path}")

    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    model_path = 'efficientdet_lite0.tflite'
    if not os.path.exists(model_path):
        print("❌ 無法找到模型：efficientdet_lite0.tflite")
        return

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.ObjectDetectorOptions(
        base_options=base_options,
        score_threshold=0.5
    )
    detector = vision.ObjectDetector.create_from_options(options)

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    results_all = []

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    raw_output_video_path = output_video_path.replace('.mp4', '_raw.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(raw_output_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(image)

        object_data = []
        for det in result.detections:
            bbox = det.bounding_box
            class_name = det.categories[0].category_name
            score = det.categories[0].score

            x1, y1 = bbox.origin_x, bbox.origin_y
            x2, y2 = x1 + bbox.width, y1 + bbox.height

            object_data.append({
                'class': class_name,
                'score': round(float(score), 2),
                'bbox': {
                    'x_min': x1,
                    'y_min': y1,
                    'width': bbox.width,
                    'height': bbox.height
                }
            })

            # 畫出框與標籤
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label_text = f"{class_name} {score:.2f}"
            cv2.putText(frame, label_text, (x1, max(10, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        results_all.append({
            'frame': frame_count,
            'objects': object_data
        })

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results_all, f, indent=2)

    convert_to_h264(raw_output_video_path, output_video_path)