from PySide2 import QtWidgets
from PySide2.QtCore import QTimer, Slot, Signal, QThread, QRegExp
from PySide2.QtGui import QRegExpValidator
from gui.image_view import ImageView
from workers.camera_worker import CameraWorker
import os
from time import time


class MainWindow(QtWidgets.QWidget):
    tick_signal = Signal()

    def __init__(self):
        super(MainWindow, self).__init__()

        postfix = '_best_weights'
        self.models = {}
        models_weights = os.listdir('./result')
        for filename in models_weights:
            if postfix in filename:
                model_name = filename.split(postfix)[0]
                self.models[model_name] = {
                    'weights': filename,
                    'widget_label': QtWidgets.QLabel(model_name),
                    'widget_value': QtWidgets.QLabel('0.0')
                }
                self.models[model_name]['widget_value'].setDisabled(True)

        self.image_view = ImageView()

        self.camera_id_label = QtWidgets.QLabel('Camera ID: ')
        self.camera_id_input = QtWidgets.QSpinBox()
        self.camera_id_input.setValue(0)

        # self.max_fps_label = QtWidgets.QLabel('Max FPS: ')
        # self.max_fps_input = QtWidgets.QLineEdit('5.0')
        # rx = QRegExp('^\\d+(.\\d+)?$')
        # validator = QRegExpValidator(rx, self)
        # self.max_fps_input.setValidator(validator)
        # self.max_fps_input.textChanged.connect(self.set_max_fps)

        self.fps_label = QtWidgets.QLabel('FPS: ')
        self.fps_value = QtWidgets.QLineEdit()
        self.fps_value.setDisabled(True)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.image_view, 0, 0, 30, 1)
        layout.addWidget(self.camera_id_label, 0, 1)
        layout.addWidget(self.camera_id_input, 0, 2)
        # layout.addWidget(self.max_fps_label, 1, 1)
        # layout.addWidget(self.max_fps_input, 1, 2)
        layout.addWidget(self.fps_label, 1, 1)
        layout.addWidget(self.fps_value, 1, 2)
        row = 2
        for key, value in self.models.items():
            layout.addWidget(value['widget_label'], row, 1)
            layout.addWidget(value['widget_value'], row, 2)
            row += 1
        self.setLayout(layout)

        self.camera_worker = CameraWorker()
        self.camera_worker.new_frame_signal.connect(self.image_view.set_image)
        self.camera_id_input.valueChanged.connect(self.camera_worker.set_camera)
        self.tick_signal.connect(self.camera_worker.take_camera_frame)

        self.threads = []
        self.threads.append(QThread())
        self.camera_worker.moveToThread(self.threads[-1])

        for t in self.threads:
            t.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick_signal)
        self.camera_worker.new_frame_signal.connect(self.calculate_fps)
        self.last_time = 0
        self.set_max_fps(5)

    @Slot(str)
    def set_max_fps(self, max_fps):
        self.timer.stop()
        max_fps = float(max_fps)
        if max_fps != 0:
            self.timer.start(int(1000 / max_fps))

    @Slot()
    def calculate_fps(self):
        current_time = int(time() * 1000)
        dt = current_time - self.last_time
        if dt != 0:
            fps = round(1000 / dt, 1)
        else:
            fps = 999
        self.fps_value.setText(str(fps))
        self.last_time = current_time

    def closeEvent(self, event):
        for t in self.threads:
            t.quit()
            t.wait()
