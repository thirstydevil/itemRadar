__author__ = 'David'

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

    splash_pix = QtGui.QPixmap(radarUI.g_IMAGES_PATH + "/windowIcon.png")
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    time.sleep(.5)

    splash.close()
    ui = radarUI.MainWindow()
    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
