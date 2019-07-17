from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from gui.main_window import MainWindow
from gui.video_window import VideoWindow


class NeuralMirrorApplication(QApplication):

    def __init__(self):
        super().__init__([])
        self.main_window = MainWindow()
        self.main_window.setAttribute(Qt.WA_DeleteOnClose, True)
        self.main_window.destroyed.connect(self.quit)
        self.video_window = VideoWindow()
        self.video_window.closed_signal.connect(self.enable_video_button)

        self.main_window.video_button_pressed_signal.connect(self.show_video_window)

    def show_video_window(self):
        self.main_window.video_widget_button.setDisabled(True)
        self.video_window.showFullScreen()

    def enable_video_button(self):
        self.main_window.video_widget_button.setDisabled(False)
