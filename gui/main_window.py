from PySide2 import QtWidgets
from PySide2.QtCore import QTimer, Signal, QThread, Slot
from gui.image_view import ImageView
from workers.camera_worker import CameraWorker
from workers.qt_agent_worker import QtAgentWorker
from workers.model_worker import ModelWorker
# import os
from time import time


class MainWindow(QtWidgets.QWidget):
    init_signal = Signal()
    # tick_signal = Signal()

    last_tick_time = 0
    tick_timeout = 200
    max_fps = 5

    # models = {}
    model = {}

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

        model_layout = QtWidgets.QGridLayout()
        self.scan_model()
        self.model['widgets'] = {}
        i = 0
        for label in self.model['labels']:
            label_widget = QtWidgets.QLabel(f'{label}: ')
            value_widget = QtWidgets.QLabel(' - ')
            value_widget.setDisabled(True)
            value_widget.setMinimumWidth(50)
            model_layout.addWidget(label_widget, i, 0)
            model_layout.addWidget(value_widget, i, 1)
            i += 1
            self.model['widgets'][label] = {
                'label': label_widget,
                'value': value_widget
            }

        panel_layout = QtWidgets.QVBoxLayout()
        panel_layout.addLayout(instruments_layout)
        panel_layout.addLayout(model_layout)
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
        # Model
        self.model_worker = ModelWorker(self.model['labels'], self.model['weights'])
        self.model_worker.model_loaded_signal.connect(self.connect_loaded_model)
        self.camera_worker.new_frame_signal.connect(self.model_worker.predict)
        self.model_worker.predict_result_signal.connect(self.update_predict_result)
        # for model_label, model_data in self.models.items():
        #     model_worker = ModelWorker(model_label, model_data['file'])
        #     model_worker.model_loaded_signal.connect(self.connect_loaded_models)
        #     model_worker.predict_result_signal.connect(self.update_predict_result)
        #     model_data['worker'] = model_worker

        # Timer
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.camera_worker.take_camera_frame)

        # Threads
        self.threads = []
        workers = [self.camera_worker, self.qt_agent_worker, self.model_worker]
        # for model_label, model_data in self.models.items():
        #     workers.append(model_data['worker'])
        for w in workers:
            self.threads.append(QThread())
            w.moveToThread(self.threads[-1])
            self.threads[-1].start()

        # Init
        self.init_signal.connect(self.camera_worker.set_camera)
        self.init_signal.connect(self.model_worker.init)
        # for model_label, model_data in self.models.items():
        #     # noinspection PyUnresolvedReferences
        #     self.init_signal.connect(model_data['worker'].init)
        self.init_signal.emit()

        # self.qt_agent_worker.new_image_signal.connect(self.tick_finish)
        # self.tick_start()

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

    def scan_model(self):
        self.model['weights'] = './result/best_weights.h5'
        with open('./result/labels.txt') as file:
            self.model['labels'] = file.read().split('\n')

    @Slot()
    def connect_loaded_model(self):
        self.tick_start()
    #     self.models_result_count += 1
    #     if self.models_result_count == self.models_count:
    #         for _, model_data in self.models.items():
    #             # noinspection PyUnresolvedReferences
    #             self.camera_worker.new_frame_signal.connect(model_data['worker'].predict)
    #         self.models_result_count = 0
    #         self.tick_start()

    @Slot(dict)
    def update_predict_result(self, result: dict):
        for key, value in result.items():
            self.model['widgets'][key]['value'].setText(f'{value} %')
        self.tick_finish()
    #     # noinspection PyUnresolvedReferences
    #     self.models[model_name]['value_widget'].setText(str(round(predict_result, 2)))
    #
    #     self.models_result_count += 1
    #     if self.models_result_count == self.models_count:
    #         self.models_result_count = 0
    #         self.tick_finish()

    def closeEvent(self, event):
        for t in self.threads:
            t.quit()
            t.wait()
