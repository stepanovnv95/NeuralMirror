from PySide2.QtWidgets import QWidget, QLabel, QSpinBox, QPushButton
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
from PySide2.QtCore import Signal
from gui.image_view import ImageView


class MainWindow(QWidget):
    video_button_pressed_signal = Signal()
    camera_id_changed_signal = Signal(int)
    max_fps_changed_signal = Signal(int)
    labels_widgets = {}

    def __init__(self, labels: list):
        super().__init__()

        self.image_view = ImageView()
        self.camera_id_label = QLabel('Camera ID: ')
        self.camera_id_input = QSpinBox()
        self.camera_id_input.valueChanged.connect(self.camera_id_changed_signal)
        self.max_fps_label = QLabel('Max FPS: ')
        self.max_fps_input = QSpinBox()
        self.max_fps_input.setValue(5)
        self.max_fps_input.valueChanged.connect(self.max_fps_changed_signal)
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

        labels_layout = QGridLayout()
        i = 0
        for l in labels:
            label_label = QLabel(l)
            label_value = QLabel(' - ')
            label_value.setMinimumWidth(50)
            labels_layout.addWidget(label_label, i, 0)
            labels_layout.addWidget(label_value, i, 1)
            self.labels_widgets[l] = {
                'label_widget': label_label,
                'value_widget': label_value
            }
            i += 1

        right_block_layout = QVBoxLayout()
        right_block_layout.addLayout(tools_layout)
        right_block_layout.addLayout(labels_layout)
        right_block_layout.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(self.image_view, 1)
        layout.addLayout(right_block_layout)
        self.setLayout(layout)

    def set_fps_value(self, fps: int):
        self.fps_value.setText(str(fps))

    def get_max_fps(self) -> int:
        return self.max_fps_input.value()

    def set_frame(self, image):
        self.image_view.set_image(image)

    def set_predict_values(self, predict_dict: dict):
        for key, value in predict_dict.items():
            self.labels_widgets[key]['value_widget'].setText(str(value))
