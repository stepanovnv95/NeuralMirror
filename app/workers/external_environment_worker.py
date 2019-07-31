from PySide2.QtCore import QObject, Signal, Slot, QTimer
import configparser
import datetime


class ExternalEnvironmentWorker(QObject):

    ex_environment_labels_signal = Signal(list)

    def __init__(self):
        super().__init__()

        config = configparser.ConfigParser()
        config.read('../config.ini')

        self.morning, self.afternoon, self.evening = self.get_times_from_config(config)

        self.update_info()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(int(config['timers']['update_environment_timeout']) * 1000)

    @staticmethod
    def get_times_from_config(config):
        for daytime in ['morning', 'afternoon', 'evening']:
            x = config['day'][daytime].split('-')
            x = [x.split(':') for x in x]
            yield tuple(datetime.time(int(h), int(m)) for h, m in x)

    @Slot()
    def update_info(self):
        labels = ['common']
        now_time = datetime.datetime.now().time()
        if self.morning[0] <= now_time <= self.morning[1]:
            labels.append('morning')
        if self.afternoon[0] <= now_time <= self.afternoon[1]:
            labels.append('afternoon')
        if self.evening[0] <= now_time <= self.evening[1]:
            labels.append('evening')
        self.ex_environment_labels_signal.emit(labels)
