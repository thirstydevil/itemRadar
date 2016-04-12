__author__ = 'davidm'

import radarUI
from PySide import QtGui, QtCore
import sys
import qdarkstyle
import time


def main():
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication(sys.argv)
        app.setStyleSheet(qdarkstyle.load_stylesheet())
    ui = radarUI.MainWindow()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
