from .abstract_worker import AbstractWorker
from os import path
import os
from PySide2.QtCore import Signal, Slot, QTimer
import random


class VideoStarterWorker(AbstractWorker):

    set_video_signal = Signal(str)

    videos_path = './videos/'
    videos = {}
    blocked = False
    no_one_timer = QTimer()
    no_one_timeout = (5 * 1000, 10 * 1000)

    def __init__(self, labels: list, no_one_label: str):
        super().__init__()
        self.last_label = no_one_label
        self.labels = labels
        self.no_one_label = no_one_label
        self.scan_videos()
        self.no_one_timer.setSingleShot(True)

    def scan_videos(self):
        for l in self.labels:
            videos_path = path.join(self.videos_path, l)
            if l == self.no_one_label:
                videos_path = path.join(videos_path, 'common')
            videos_files = os.listdir(videos_path)
            videos_files = list(map(lambda x: path.join(videos_path, x), videos_files))
            self.videos[l] = videos_files

    @Slot(dict)
    def update_predict_results(self, predict_results: dict):
        label = self.last_label
        for key, value in predict_results.items():
            if value == 1:
                label = key
                break
        if label != self.last_label:
            self.last_label = label
            self.start_video(label)

    def start_video(self, label: str):
        if self.blocked or label == self.no_one_label:
            return
        self.blocked = True
        videos = self.videos[label]
        v = videos[random.randint(0, len(videos) - 1)]
        self.set_video_signal.emit(v)

    @Slot()
    def unblock(self):
        self.blocked = False
