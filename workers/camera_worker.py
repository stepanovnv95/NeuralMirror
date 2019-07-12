from PySide2.QtCore import QObject, Slot, Signal #, QTimer
# from PySide2.QtGui import QPixmap, QImage
import cv2
import numpy as np


class CameraWorker(QObject):
    new_frame_signal = Signal(np.ndarray)

    camera = None

    def __init__(self):
        super().__init__()

    @Slot(int)
    def set_camera(self, camera_id=0):
        if self.camera is not None:
            self.camera.release()
        self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

    def take_camera_frame(self):
        pass
        if self.camera is None:
            return
        check, frame = self.camera.read()
        if not check:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.new_frame_signal.emit(frame)
