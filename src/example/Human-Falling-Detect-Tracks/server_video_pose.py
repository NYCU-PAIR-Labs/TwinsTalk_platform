import pika, sys, os, io
import numpy as np
import cv2
import torch

from DetectorLoader import TinyYOLOv3_onecls
from PoseEstimateLoader import SPPE_FastPose

class Detector():
    def __init__(self) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # DETECTION MODEL.
        inp_dets = 384
        self.detect_model = TinyYOLOv3_onecls(inp_dets, device=self.device)

        # POSE MODEL.
        inp_pose = ["224", "160"]
        inp_pose = (int(inp_pose[0]), int(inp_pose[1]))
        self.pose_model = SPPE_FastPose("resnet50", inp_pose[0], inp_pose[1], device=self.device)

    def yolo_detect(self, img):
        # Detect humans bbox in the frame with detector model.
        detected = self.detect_model.detect(img, need_resize=True, expand_bb=10)

        # crop image with human bbox
        if detected is not None:
            for bbox in detected:
                croped = img[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
                return croped
            
        return None

    def pose_detect(self, img):
        poses = self.pose_model.predict(img, torch.tensor([[0, 0, img.shape[1], img.shape[0]]]), torch.tensor([[1]]))
        if poses:
            return poses
        return None
    
    def detect(self, video):
        cap = cv2.VideoCapture(video)
        rankles = []
        while(cap.isOpened()):
            ret, frame = cap.read()

            if ret:
                croped = self.yolo_detect(frame)

                if croped is not None:
                    pose = self.pose_detect(croped)
                    if pose:
                        rankles.append(pose[0]["keypoints"][-1][1].numpy())
            
            else:
                break

        return np.concatenate(rankles, axis=None)

class PoseDetector():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="Pose", exchange_type="topic", auto_delete=True, arguments={"output":["Pose_output_nparray", "Pose_output_text"]})
        self.channel.queue_declare(queue='Pose_input_video', exclusive=True)
        self.channel.queue_bind(queue="Pose_input_video", exchange="Pose", routing_key=f"*.*.*.video")

        self.detector = Detector()
        self.count = 0

    def __callback(self, ch, method, properties, body):
        if "Pose" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            # Write your service from here
            print(f"receivce from {client_id}")
            with open(f"./Video/{method.routing_key}.mp4", "wb") as binary_file:
                binary_file.write(body)

            result = self.detector.detect(f"./Video/{method.routing_key}.mp4")

            if result is not None:
                print(f"Write result to {app_name}.{client_id}")
                self.channel.basic_publish(exchange="Pose",
                                           routing_key=f"{app_name}.{client_id}.Pose.nparray",
                                           body=result.tobytes())
                self.channel.basic_publish(exchange="Pose",
                                           routing_key=f"{app_name}.{client_id}.Pose.text",
                                           body=str(result))


    def run(self):
        self.channel.basic_consume(queue='Pose_input_video', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = PoseDetector()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
