from PySide2 import QtWidgets, QtCore, QtGui


class ImageView(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()

        # noinspection PyArgumentList
        self.setMinimumSize(500, 500)

        self.setStyleSheet('background: black')
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.original_image = QtGui.QPixmap()

    def set_image(self, pixmap):
        self.original_image = pixmap
        self._fit_image()

    def _fit_image(self):
        """
        Try to fit image in widget size
        """
        if self.original_image.isNull():
            image = None
        else:
            image = self.original_image.scaled(self.width(), self.height(),
                                               QtCore.Qt.KeepAspectRatio)
        self.setPixmap(image)

    def resizeEvent(self, event):
        self._fit_image()
