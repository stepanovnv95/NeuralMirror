from PySide2.QtCore import QObject, Slot, Signal
from model import InceptionModel
import numpy as np
import cv2


class ModelWorker(QObject):
    model_loaded_signal = Signal()
    predict_result_signal = Signal(dict)

    model = None

    def __init__(self, labels: list, weights_file: str):
        super().__init__()
        self.labels = labels
        self.weights_file = weights_file

    @Slot()
    def init(self):
        self.model = InceptionModel(len(self.labels), False)
        self.model.load(self.weights_file)
        self.model_loaded_signal.emit()
        print(f'Model loaded from {self.weights_file}')

    @Slot(np.ndarray)
    def predict(self, image):
        height, weight, _ = image.shape
        square_size = min(height, weight)
        if weight >= height:
            offset = int((weight - height) / 2)
            image = image[:, offset:offset + square_size]
        else:
            image = image[:square_size, :]
        # image = cv2.resize(image, (299, 299))
        image = cv2.resize(image, (224, 224))
        image = image / 255.0

        image = np.expand_dims(image, axis=0)
        result = self.model.predict(image)[0]
        dict_result = {}
        for i in range(len(self.labels)):
            dict_result[self.labels[i]] = int(round(result[i] * 100))
        self.predict_result_signal.emit(dict_result)
