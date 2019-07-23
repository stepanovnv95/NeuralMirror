from workers.abstract_worker import AbstractWorker
from PySide2.QtCore import Signal, Slot
import cv2
import numpy as np


class CameraWorker(AbstractWorker):
    new_frame_signal = Signal(np.ndarray)

    camera = None

    @Slot()
    def init_slot(self):
        self.set_camera(0)
        super().init_slot()

    @Slot(int)
    def set_camera(self, camera_id):
        if self.camera is not None:
            self.camera.release()
        self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

    @Slot()
    def close_slot(self):
        self.camera.release()

    @staticmethod
    def _get_black_frame() -> np.ndarray:
        return np.zeros((1, 1, 3))

    @Slot()
    def take_camera_frame(self):
        if self.camera is None:
            self.new_frame_signal.emit(self._get_black_frame())

        check, frame = self.camera.read()

        if not check:
            self.new_frame_signal.emit(self._get_black_frame())
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.new_frame_signal.emit(frame)
