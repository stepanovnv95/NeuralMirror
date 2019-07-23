from PySide2.QtCore import QObject, Signal, Slot
from time import time


class FilterWorker(QObject):

    predict_values_updated_signal = Signal(dict)

    def __init__(self, labels:list):
        super().__init__()
        self.labels = dict((key, 0.0) for key in labels)
        self.default_key = 'no_one'
        self.last_time = time()
        self.kt = 2.0

    @Slot(dict)
    def update_predict_values(self, predict_dict:dict):
        current_time = time()
        dt = current_time - self.last_time
        dt = min(dt, self.kt)
        dv = dt / self.kt
        self.last_time = current_time
        max_label = self.default_key if self.default_key in self.labels.keys() else list(self.labels.keys())[0]
        max_value = 0.0
        for key, value in predict_dict.items():
            if value > 0.7:
                self.labels[key] += dv
                self.labels[key] = min(self.labels[key], 1.0)
            else:
                self.labels[key] -= dv
                self.labels[key] = max(self.labels[key], 0.0)
            if self.labels[key] > max_value:
                max_label, max_value = key, self.labels[key]
        result = dict((key, 0) for key, _ in self.labels.items())
        result[max_label] = 1
        self.predict_values_updated_signal.emit(result)
