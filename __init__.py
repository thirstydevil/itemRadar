__author__ = 'David'

import radarUI
from PyQt4 import QtGui
import sys


def main():
    app = QtGui.QApplication.instance()
    if not app:
        app = QtGui.QApplication(sys.argv)

    ui = radarUI.MainDialog()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
