import pika, sys, os
import numpy as np
import cv2
import torch

from Detection.Utils import ResizePadding
from CameraLoader import CamLoader, CamLoader_Q
from DetectorLoader import TinyYOLOv3_onecls

from PoseEstimateLoader import SPPE_FastPose
from fn import draw_single

from Track.Tracker import Detection, Tracker
from ActionsEstLoader import TSSTG

class HAR():
    def __init__(self, clientID) -> None:
        self.clientID = clientID
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        # DETECTION MODEL.
        inp_dets = 384
        self.detect_model = TinyYOLOv3_onecls(inp_dets, device=self.device)

        # POSE MODEL.
        inp_pose = ["224", "160"]
        inp_pose = (int(inp_pose[0]), int(inp_pose[1]))
        self.pose_model = SPPE_FastPose("resnet50", inp_pose[0], inp_pose[1], device=self.device)

        # Tracker.
        max_age = 30
        self.tracker = Tracker(max_age=max_age, n_init=3)

        # Actions Estimate.
        self.action_model = TSSTG()
        self.resize_fn = ResizePadding(inp_dets, inp_dets)

    def kpt2bbox(self, kpt, ex=20):
        """Get bbox that hold on all of the keypoints (x,y)
        kpt: array of shape `(N, 2)`,
        ex: (int) expand bounding box,
        """
        return np.array((kpt[:, 0].min() - ex, kpt[:, 1].min() - ex,
                        kpt[:, 0].max() + ex, kpt[:, 1].max() + ex))

    def detect(self, img):
        # Detect humans bbox in the frame with detector model.
        detected = self.detect_model.detect(img, need_resize=True, expand_bb=10)

        # Predict each tracks bbox of current frame from previous frames information with Kalman filter.
        self.tracker.predict()

        # Merge two source of predicted bbox together.
        for track in self.tracker.tracks:
            det = torch.tensor([track.to_tlbr().tolist() + [0.5, 1.0, 0.0]], dtype=torch.float32)
            detected = torch.cat([detected, det], dim=0) if detected is not None else det

        detections = []  # List of Detections object for tracking.
        if detected is not None:
            #detected = non_max_suppression(detected[None, :], 0.45, 0.2)[0]
            # Predict skeleton pose of each bboxs.
            poses = self.pose_model.predict(img, detected[:, 0:4], detected[:, 4])

            # Create Detections object.
            detections = [Detection(self.kpt2bbox(ps['keypoints'].numpy()),
                                    np.concatenate((ps['keypoints'].numpy(),
                                                    ps['kp_score'].numpy()), axis=1),
                                    ps['kp_score'].mean().numpy()) for ps in poses]

            # Update tracks by matching each track information of current and previous frame or
            # create a new track if no matched.
            self.tracker.update(detections)

            # Predict Actions of each track.
            for i, track in enumerate(self.tracker.tracks):
                if not track.is_confirmed():
                    continue

                track_id = track.track_id
                bbox = track.to_tlbr().astype(int)
                center = track.get_center().astype(int)

                action = 'pending..'
                # Use 30 frames time-steps to prediction.
                if len(track.keypoints_list) == 30:
                    pts = np.array(track.keypoints_list, dtype=np.float32)
                    out = self.action_model.predict(pts, img.shape[:2])
                    action_name = self.action_model.class_names[out[0].argmax()]
                    action = f"ClientID:{self.clientID}, TrackID:{track_id}, Action:{action_name}, Probability:{out[0].max()*100:.2f}"
                    print(action)
                    if action_name == "Lying Down":
                        return action
        return None

class FallDetectorGCN():
    def __init__(self) -> None:
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='140.113.193.10', port=5672))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange="FallDetectorGCN", exchange_type="topic", auto_delete=True)
        self.channel.queue_declare(queue='FallDetectorGCN_input_file', exclusive=True)
        self.channel.queue_bind(queue="FallDetectorGCN_input_file", exchange="FallDetectorGCN", routing_key=f"*.*.*.file")

        self.client_detector = {}

    def __callback(self, ch, method, properties, body):
        if "FallDetectorGCN" in method.routing_key:
            pass
        else:
            routing_key_tokens = method.routing_key.split(".")
            app_name = routing_key_tokens[0]
            client_id = routing_key_tokens[1]

            if client_id not in self.client_detector.keys():
                self.client_detector[client_id] = HAR(client_id)
                print(f"Add new client: {client_id}")

            # Write your service from here
            img_bytes = np.frombuffer(body, dtype=np.uint8)
            img = cv2.imdecode(img_bytes, 1)

            result = self.client_detector[client_id].detect(img)
            if result:
                print(f"Detect {app_name}.{client_id} FALL!")
                self.channel.basic_publish(exchange="FallDetectorGCN",
                                           routing_key=f"{app_name}.{client_id}.FallDetectorGCN.text",
                                           body=result)


    def run(self):
        self.channel.basic_consume(queue='FallDetectorGCN_input_file', on_message_callback=self.__callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()

if __name__ == '__main__':
    try:
        detector = FallDetectorGCN()
        detector.run()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)