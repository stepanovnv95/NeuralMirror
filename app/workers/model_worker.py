from workers.abstract_worker import AbstractWorker
from PySide2.QtCore import Signal, Slot
import numpy as np
import cv2
from model.model import ClassificationModel


class ModelWorker(AbstractWorker):
    predict_result_signal = Signal(dict)

    model: ClassificationModel = None

    def __init__(self, labels: list, weights_file: str):
        super().__init__()
        self.labels = labels
        self.weights_file = weights_file

    @Slot()
    def init_slot(self):
        self.model = ClassificationModel(len(self.labels), False)
        self.model.load(self.weights_file)
        print(f'Model loaded from {self.weights_file}')
        super().init_slot()

    @Slot(np.ndarray)
    def predict(self, image: np.ndarray):
        height, weight, _ = image.shape
        square_size = min(height, weight)
        if weight >= height:
            offset = int((weight - height) / 2)
            image = image[:, offset:offset + square_size]
        else:
            image = image[:square_size, :]
        image = cv2.resize(image, tuple(self.model.image_size))
        image = image / 255.0

        image = np.expand_dims(image, axis=0)
        result = self.model.predict(image)[0]
        dict_result = {}
        for i in range(len(self.labels)):
            dict_result[self.labels[i]] = round(result[i], 2)
        self.predict_result_signal.emit(dict_result)
