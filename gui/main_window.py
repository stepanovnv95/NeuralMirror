from PySide2.QtWidgets import QWidget, QLabel, QSpinBox, QPushButton
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
from PySide2.QtCore import Signal
from gui.image_view import ImageView


class MainWindow(QWidget):
    video_button_pressed_signal = Signal()

    def __init__(self):
        super().__init__()

        self.image_view = ImageView()
        self.camera_id_label = QLabel('Camera ID: ')
        self.camera_id_input = QSpinBox()
        self.max_fps_label = QLabel('Max FPS: ')
        self.max_fps_input = QSpinBox()
        self.max_fps_input.setValue(10)
        self.fps_label = QLabel('FPS: ')
        self.fps_value = QLabel(' - ')
        self.fps_value.setDisabled(True)
        self.video_widget_button = QPushButton('Enable video mode')
        self.video_widget_button.clicked.connect(self.video_button_pressed_signal)

        tools_layout = QGridLayout()
        tools_layout.addWidget(self.camera_id_label, 0, 0)
        tools_layout.addWidget(self.camera_id_input, 0, 1)
        tools_layout.addWidget(self.max_fps_label, 1, 0)
        tools_layout.addWidget(self.max_fps_input, 1, 1)
        tools_layout.addWidget(self.fps_label, 2, 0)
        tools_layout.addWidget(self.fps_value, 2, 1)
        tools_layout.addWidget(self.video_widget_button, 3, 0, 1, 2)

        right_block_layout = QVBoxLayout()
        right_block_layout.addLayout(tools_layout)
        right_block_layout.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.image_view, 1)
        layout.addLayout(right_block_layout)
        self.setLayout(layout)
