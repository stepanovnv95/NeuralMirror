from PySide2.QtCore import Qt, QTimer, Signal, QUrl
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtMultimedia import QMediaPlayer
from PySide2.QtWidgets import QWidget, QLabel
from PySide2.QtWidgets import QGridLayout
from PySide2.QtGui import QKeyEvent


class VideoWindow(QWidget):
    closed_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet('QWidget { background: black }')

        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        layout = QGridLayout()
        layout.addWidget(self.video_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.info_label = QLabel('Press ESC to exit from fullscreen mode', self)
        self.info_label.setStyleSheet('QLabel { color: white }')
        self.info_label.hide()

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.info_label.hide)

    def showFullScreen(self):
        super().showFullScreen()
        self.info_label.setGeometry(0, 0, self.width(), 50)
        self.info_label.show()
        self.timer.start(10 * 1000)
        self.test_play_video()

    def keyPressEvent(self, event:QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.timer.stop()
            self.player.stop()
            self.closed_signal.emit()
            self.close()

    def test_play_video(self):
        self.player.setMedia(QUrl.fromLocalFile('./videos/Imoar.mp4'))
        self.player.play()
