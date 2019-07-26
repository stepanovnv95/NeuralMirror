import os
import sys
from app import NeuralMirrorApplication


# def excepthook(cls, exception, traceback):
#     print('calling excepthook...')
#     print("{}".format(exception))


if __name__ == '__main__':
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '../python/Libs/site-packages/PySide2/plugins'
    # sys.excepthook = excepthook
    app = NeuralMirrorApplication()
    app.main_window.show()
    sys.exit(app.exec_())
