import numpy as np
import cv2 as cv
from pose_engine import PoseEngine
from direct.distributed.PyDatagram import PyDatagram
from panda3d.core import QueuedConnectionManager, ConnectionWriter, NetAddress

TRESHOLD = 0.5
SERVER_PORT = 9099 # same for client and server
SERVER_IP = "ha.doma" #"ha.doma"
TIMEOUT = 3000  # How long, in milliseconds, until we give up trying to reach the server?

KEYS= {
  'nose': 17,
  'left ear': 1,
  'right ear': 2,
  'left eye': 3,
  'right eye': 4,
  'left shoulder': 5,
  'right shoulder': 6,
  'left elbow': 7,
  'right elbow': 8,
  'left wrist': 9,
  'right wrist': 10,
  'left hip': 11,
  'right hip': 12,
  'left knee': 13,
  'right knee': 14,
  'left ankle': 15,
  'right ankle': 16
}


class PoseGameClient():

    def __init__(self):
        model = 'models/mobilenet/posenet_mobilenet_v1_075_481_641_quant_decoder_edgetpu.tflite'
        self.engine = PoseEngine(model)
        self.input_shape = self.engine.get_input_tensor_shape()  #641x481x3
        print(f"Model input shape {self.input_shape}")
        inference_size = (self.input_shape[2], self.input_shape[1])

        cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            exit()

        cManager = QueuedConnectionManager()
        self.cWriter = ConnectionWriter(cManager, 0)
        print("Connecting to tcp://{}:{}, timeout={}".format(SERVER_IP, SERVER_PORT, TIMEOUT))
        self.connection = cManager.openTCPClientConnection(SERVER_IP, SERVER_PORT, TIMEOUT) 
        if self.connection:
            print("Connected")
            count = 0
            while True:
                ret, frame = cap.read() #(480, 640, 3)
                if not ret:
                    print("Can't receive frame (stream end?). Exiting ...")
                    break
                self.infer(frame)
                if cv.waitKey(1) == ord('q'):
                    break


    def send_pose(self, pose):
        myPyDatagram = PyDatagram()
        for label, keypoint in pose.keypoints.items():
            if keypoint.score < TRESHOLD: continue
            keyId = KEYS.get(label)
            myPyDatagram.addUint8(keyId)
            myPyDatagram.addFloat64(keypoint.yx[0])
            myPyDatagram.addFloat64(keypoint.yx[1])
        myPyDatagram.addUint8(255)  # Indicate end of datagram
        self.cWriter.send(myPyDatagram, self.connection)
        return


    def infer(self,frame):
        global input_shape
        input_tensor = cv.resize(frame, (self.input_shape[2], self.input_shape[1]), interpolation = cv.INTER_AREA).flatten()
        output = self.engine.run_inference(input_tensor)
        outputs, inference_time = self.engine.ParseOutput(output)
        for pose in outputs: # assume one person only
            self.send_pose(pose)
            return

    def destroy(self):
        self.cWriter.shutdown()
        if self.cWriter.getManager():
            self.cWriter.getManager().closeConnection(self.connection)


if __name__ == '__main__':
    try:
        app = PoseGameClient()
        app.destroy()
    except SystemExit:
        app.destroy()
