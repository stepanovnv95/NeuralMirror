import sys
from PySide2 import QtWidgets
from gui.main_window import MainWindow
import os

# some computers cannot find Qt components
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = 'env/Lib/site-packages/PySide2/plugins'


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
