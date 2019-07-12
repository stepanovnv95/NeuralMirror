from PySide2 import QtWidgets
from PySide2.QtCore import QTimer, Signal, QThread, Slot
from gui.image_view import ImageView
from workers.camera_worker import CameraWorker
from workers.qt_agent_worker import QtAgentWorker
from workers.model_worker import ModelWorker
import os
from time import time


class MainWindow(QtWidgets.QWidget):
    init_signal = Signal()
    tick_signal = Signal()

    last_tick_time = 0
    tick_timeout = 100
    max_fps = 10

    models = {}

    def __init__(self):
        super(MainWindow, self).__init__()

        # GUI
        self.image_view = ImageView()

        self.camera_id_label = QtWidgets.QLabel('Camera ID: ')
        self.camera_id_input = QtWidgets.QSpinBox()

        self.max_fps_label = QtWidgets.QLabel('Max FPS: ')
        self.max_fps_input = QtWidgets.QSpinBox()
        self.max_fps_input.setValue(self.max_fps)
        self.max_fps_input.valueChanged.connect(self.set_max_fps)

        self.fps_label = QtWidgets.QLabel('FPS: ')
        self.fps_output = QtWidgets.QLabel(' - ')
        self.fps_output.setDisabled(True)

        instruments_layout = QtWidgets.QGridLayout()
        instruments_layout.addWidget(self.camera_id_label, 0, 0)
        instruments_layout.addWidget(self.camera_id_input, 0, 1)
        instruments_layout.addWidget(self.max_fps_label, 1, 0)
        instruments_layout.addWidget(self.max_fps_input, 1, 1)
        instruments_layout.addWidget(self.fps_label, 2, 0)
        instruments_layout.addWidget(self.fps_output, 2, 1)

        models_layout = QtWidgets.QGridLayout()
        self.scan_models()
        i = 0
        for model_label, model_data in self.models.items():
            label_widget = QtWidgets.QLabel(f'{model_label}: ')
            value_widget = QtWidgets.QLabel(' - ')
            value_widget.setDisabled(True)
            models_layout.addWidget(label_widget, i, 0)
            models_layout.addWidget(value_widget, i, 1)
            i += 1
            model_data['label_widget'] = label_widget
            model_data['value_widget'] = value_widget
        self.models_count = len(self.models.keys())
        self.models_result_count = 0

        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.addLayout(instruments_layout)
        panel_layout.addLayout(models_layout)
        panel_layout.addStretch(1)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.image_view, 1)
        layout.addLayout(panel_layout)
        self.setLayout(layout)

        # Workers
        # Camera
        self.camera_worker = CameraWorker()
        self.camera_id_input.valueChanged.connect(self.camera_worker.set_camera)
        # Qt agent
        self.qt_agent_worker = QtAgentWorker()
        self.camera_worker.new_frame_signal.connect(self.qt_agent_worker.image_numpy_to_qt)
        self.qt_agent_worker.new_image_signal.connect(self.image_view.set_image)
        # Models
        for model_label, model_data in self.models.items():
            model_worker = ModelWorker(model_label, model_data['file'])
            model_worker.model_loaded_signal.connect(self.connect_loaded_models)
            model_worker.predict_result_signal.connect(self.update_predict_result)
            model_data['worker'] = model_worker

        # Timer
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.camera_worker.take_camera_frame)

        # Threads
        self.threads = []
        workers = [self.camera_worker, self.qt_agent_worker]
        for model_label, model_data in self.models.items():
            workers.append(model_data['worker'])
        for w in workers:
            self.threads.append(QThread())
            w.moveToThread(self.threads[-1])
            self.threads[-1].start()

        # Init
        self.init_signal.connect(self.camera_worker.set_camera)
        for model_label, model_data in self.models.items():
            # noinspection PyUnresolvedReferences
            self.init_signal.connect(model_data['worker'].init)
        self.init_signal.emit()

    def tick_start(self):
        self.timer.start(self.tick_timeout)

    @Slot()
    def tick_finish(self):
        current_tick_time = time()
        delta_time = current_tick_time - self.last_tick_time
        self.last_tick_time = current_tick_time
        current_fps = round(1 / delta_time, 1)
        self.fps_output.setText(str(current_fps))
        if current_fps != 0 and self.max_fps != 0:
            delta = (1 / self.max_fps - 1 / current_fps) * 100
            self.tick_timeout += delta
            self.tick_timeout = max(min(self.tick_timeout, 1000), 0)
        self.tick_start()

    @Slot(int)
    def set_max_fps(self, max_fps):
        self.max_fps = max_fps

    def scan_models(self):
        folder = './result'
        weights_files = os.listdir(folder)
        postfix = '_best_weights.h5'
        weights_files = list(filter(lambda x: postfix in x, weights_files))
        self.models = {}
        for wf in weights_files:
            label = wf.split(postfix)[0]
            file = os.path.join(folder, wf)
            self.models[label] = {
                'file': file
            }

    @Slot()
    def connect_loaded_models(self):
        self.models_result_count += 1
        if self.models_result_count == self.models_count:
            for _, model_data in self.models.items():
                # noinspection PyUnresolvedReferences
                self.camera_worker.new_frame_signal.connect(model_data['worker'].predict)
            self.models_result_count = 0
            self.tick_start()

    @Slot(str, float)
    def update_predict_result(self, model_name, predict_result):
        # noinspection PyUnresolvedReferences
        self.models[model_name]['value_widget'].setText(str(round(predict_result, 2)))

        self.models_result_count += 1
        if self.models_result_count == self.models_count:
            self.models_result_count = 0
            self.tick_finish()

    def closeEvent(self, event):
        for t in self.threads:
            t.quit()
            t.wait()
