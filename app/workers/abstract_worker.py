from PySide2.QtCore import QObject, Signal, Slot


class AbstractWorker(QObject):
    worker_ready_signal = Signal()

    def __init__(self):
        super().__init__()

    def init_slot(self):
        self.worker_ready_signal.emit()

    def close_slot(self):
        pass
