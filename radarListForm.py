# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\__CODE\itemRadar\resources\ui\radarListForm.ui'
#
# Created: Thu Jan 07 19:17:07 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(445, 618)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.filter_lineEdit = QtGui.QLineEdit(Form)
        self.filter_lineEdit.setObjectName("filter_lineEdit")
        self.horizontalLayout.addWidget(self.filter_lineEdit)
        self.pushButton = QtGui.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.itemTableView = QtGui.QTableView(Form)
        self.itemTableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.itemTableView.setProperty("showDropIndicator", False)
        self.itemTableView.setAlternatingRowColors(False)
        self.itemTableView.setObjectName("itemTableView")
        self.verticalLayout.addWidget(self.itemTableView)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "filter", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("Form", "Tags", None, QtGui.QApplication.UnicodeUTF8))

