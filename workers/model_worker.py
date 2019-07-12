from PySide2.QtCore import QObject, Slot
from model import InceptionBinaryModel


class ModelWorker(QObject):

    model = None

    def __init__(self, model_name, weights_file):
        super().__init__()
        self.model_name = model_name
        self.weights_file = weights_file

    @Slot()
    def init(self):
        self.model = InceptionBinaryModel(self.model_name, False)
        self.model.load(self.weights_file)
        print(f'Model {self.model_name} loaded')
