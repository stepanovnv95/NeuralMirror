from PySide2.QtCore import QObject, Signal, Slot


class FilterWorker(QObject):

    predict_values_updated_signal: Signal = Signal(dict)

    def __init__(self, labels: list):
        super().__init__()
        self.values = {l: 0.0 for l in labels}
        self.k = 0.2
        self.last_label = labels[0]
        self.hysteresis = (0.4, 0.7)

    @Slot(dict)
    def update_predict_values(self, predict_dict: dict):
        for key, value in predict_dict.items():
            self.values[key] = (1 - self.k) * self.values[key] + self.k * value
            self.values[key] = round(self.values[key], 4)

        last_label_value = self.values[self.last_label]
        if last_label_value < self.hysteresis[0]:
            max_label, max_value = self._max_in_dict(self.values)
            if max_value > self.hysteresis[1]:
                self.last_label = max_label

        result = {label: 1 if label == self.last_label else 0 for label, _ in self.values.items()}
        self.predict_values_updated_signal.emit(result)

    @staticmethod
    def _max_in_dict(d: dict):
        items = list(d.items())
        max_key, max_value = items[0]
        for key, value in items[1:]:
            if value > max_value:
                max_value = value
                max_key = key
        return max_key, max_value
