from PySide2.QtCore import QObject, Signal, Slot, QTimer
from PySide2.QtGui import QPixmap, QImage
import cv2


class CameraWorker(QObject):
    new_frame_signal = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        self.fps = 10
        self.camera = None
        self.timer = None
        self.set_camera()

    @Slot(int)
    def set_camera(self, camera_id=0):
        if self.camera is not None:
            self.camera.release()
        self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

    @Slot()
    def run(self):
        if self.timer is not None:
            self.timer.stop()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.take_camera_frame)
        self.timer.start(int(1000 / self.fps))

    def take_camera_frame(self):
        if self.camera is None:
            return
        check, frame = self.camera.read()
        if not check:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_frame = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.new_frame_signal.emit(QPixmap(q_frame))
