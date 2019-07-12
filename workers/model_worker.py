from PySide2.QtCore import QObject, Slot, Signal
from model import InceptionBinaryModel
import numpy as np
import cv2


class ModelWorker(QObject):
    model_loaded_signal = Signal()
    predict_result_signal = Signal(str, float)

    model = None

    def __init__(self, model_name, weights_file):
        super().__init__()
        self.model_name = model_name
        self.weights_file = weights_file

    @Slot()
    def init(self):
        self.model = InceptionBinaryModel(self.model_name, False)
        self.model.load(self.weights_file)
        self.model_loaded_signal.emit()
        print(f'Model {self.model_name} loaded from {self.weights_file}')

    @Slot(np.ndarray)
    def predict(self, image):
        image = cv2.resize(image, (299, 299))
        image = np.expand_dims(image, axis=0)
        result = self.model.predict(image)[0]
        self.predict_result_signal.emit(self.model_name, result)
