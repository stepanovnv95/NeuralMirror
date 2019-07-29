from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, Signal, Slot, QTimer, QThread
from gui.main_window import MainWindow
from gui.video_window import VideoWindow
from workers.camera_worker import CameraWorker
from workers.qt_converter_worker import QtConverterWorker
from workers.model_worker import ModelWorker
from workers.filter_worker import FilterWorker
from workers.video_starter_worker import VideoStarterWorker
from time import time
from os import path


class NeuralMirrorApplication(QApplication):
    tick_signal = Signal()
    close_signal = Signal()

    last_tick_time = 0
    workers_ready = 0

    def __init__(self):
        super().__init__([])

        labels, weights_file = self._scan_model_data()

        self.main_window = MainWindow(labels)
        self.main_window.setAttribute(Qt.WA_DeleteOnClose, True)
        self.main_window.destroyed.connect(self.quit)
        self.video_window = VideoWindow()
        self.video_window.closed_signal.connect(self.enable_video_button)
        self.main_window.video_button_pressed_signal.connect(self.show_video_window)
        self.main_window.max_fps_changed_signal.connect(self.set_max_fps)
        self.max_fps = self.main_window.get_max_fps()
        self.tick_timeout = int(1000 / self.max_fps)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.tick_signal)

        self.camera_worker = CameraWorker()
        self.tick_signal.connect(self.camera_worker.take_camera_frame)
        self.main_window.camera_id_changed_signal.connect(self.camera_worker.set_camera)

        self.qt_worker = QtConverterWorker()
        self.camera_worker.new_frame_signal.connect(self.qt_worker.image_numpy_to_qt)
        self.qt_worker.new_image_signal.connect(self.main_window.set_frame)

        self.model_worker = ModelWorker(labels, weights_file)
        self.camera_worker.new_frame_signal.connect(self.model_worker.predict)

        self.filter_worker = FilterWorker(labels)
        self.model_worker.predict_result_signal.connect(self.filter_worker.update_predict_values)
        self.filter_worker.predict_values_updated_signal.connect(self.main_window.set_predict_values)
        self.filter_worker.predict_values_updated_signal.connect(self.tick_finish)

        self.video_starter_worker = VideoStarterWorker(labels, 'no_one')
        self.video_window.video_stopped_signal.connect(self.video_starter_worker.unblock)

        self.threads = []
        workers = [self.camera_worker, self.qt_worker, self.model_worker]
        for w in workers:
            self.threads.append(QThread())
            self.threads[-1].started.connect(w.init_slot)
            w.worker_ready_signal.connect(self.worker_ready)
            self.close_signal.connect(w.close_slot)
            w.moveToThread(self.threads[-1])
            self.threads[-1].start()

    def show_video_window(self):
        self.main_window.video_widget_button.setDisabled(True)
        self.video_window.showFullScreen()

        self.filter_worker.predict_values_updated_signal.connect(self.video_starter_worker.update_predict_results)
        self.video_starter_worker.set_video_signal.connect(self.video_window.play_video)

    def enable_video_button(self):
        self.filter_worker.predict_values_updated_signal.disconnect(self.video_starter_worker.update_predict_results)
        self.video_starter_worker.set_video_signal.disconnect(self.video_window.play_video)

        self.main_window.video_widget_button.setDisabled(False)

    @Slot()
    def worker_ready(self):
        self.workers_ready += 1
        if self.workers_ready == len(self.threads):
            self.tick_start()

    def tick_start(self):
        self.timer.start(self.tick_timeout)

    @Slot()
    def tick_finish(self):
        current_tick_time = time()
        delta_time = current_tick_time - self.last_tick_time
        self.last_tick_time = current_tick_time
        current_fps = round(1 / delta_time, 1)
        self.main_window.set_fps_value(int(current_fps))
        if current_fps != 0 and self.max_fps != 0:
            delta = (1 / self.max_fps - 1 / current_fps) * 100
            self.tick_timeout += delta
            self.tick_timeout = max(min(self.tick_timeout, 1000), 0)
        self.tick_start()

    @Slot()
    def set_max_fps(self, max_fps: int):
        if max_fps > 0:
            self.max_fps = max_fps

    @staticmethod
    def _scan_model_data(data_path: str = '../result/'):
        weights_file = path.join(data_path, 'best_weights.h5')
        labels_file = path.join(data_path, 'labels.txt')
        with open(labels_file) as file:
            labels = file.read().split('\n')
        return labels, weights_file

    def quit(self):
        self.close_signal.emit()
        for t in self.threads:
            pass
            # t.quit()
            # t.wait()
        # поток с камерой почему-то иногда не завершается
        # поэтому просто выключаемся
        super().quit()
