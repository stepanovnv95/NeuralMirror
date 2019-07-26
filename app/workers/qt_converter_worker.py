from workers.abstract_worker import AbstractWorker
import numpy as np
from PySide2.QtCore import Signal, Slot
from PySide2.QtGui import QImage, QPixmap


class QtConverterWorker(AbstractWorker):
    new_image_signal = Signal(QPixmap)

    @Slot(np.ndarray)
    def image_numpy_to_qt(self, np_image):
        height, width, channel = np_image.shape
        bytes_per_line = 3 * width
        q_frame = QImage(np_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.new_image_signal.emit(QPixmap(q_frame))
