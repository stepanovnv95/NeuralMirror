from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtGui import QImage, QPixmap
import numpy as np


class QtAgentWorker(QObject):
    new_image_signal = Signal(QPixmap)

    def __init__(self):
        super().__init__()

    @Slot(np.ndarray)
    def image_numpy_to_qt(self, np_image):
        height, width, channel = np_image.shape
        bytes_per_line = 3 * width
        q_frame = QImage(np_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.new_image_signal.emit(QPixmap(q_frame))
