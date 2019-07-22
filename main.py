import os
import sys
from app import NeuralMirrorApplication

if __name__ == '__main__':
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = '../python/Libs/site-packages/PySide2/plugins'
    app = NeuralMirrorApplication()
    app.main_window.show()
    sys.exit(app.exec_())
