# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\__CODE\itemRadar\resources\ui\radarSelectSceneForm.ui'
#
# Created: Fri Jan 08 17:49:39 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(389, 575)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_new = QtGui.QPushButton(Form)
        self.pushButton_new.setObjectName("pushButton_new")
        self.horizontalLayout_2.addWidget(self.pushButton_new)
        self.pushButton_delete = QtGui.QPushButton(Form)
        self.pushButton_delete.setObjectName("pushButton_delete")
        self.horizontalLayout_2.addWidget(self.pushButton_delete)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit_filter = QtGui.QLineEdit(Form)
        self.lineEdit_filter.setObjectName("lineEdit_filter")
        self.horizontalLayout.addWidget(self.lineEdit_filter)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView_radarScenes = QtGui.QTableView(Form)
        self.tableView_radarScenes.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tableView_radarScenes.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView_radarScenes.setShowGrid(False)
        self.tableView_radarScenes.setSortingEnabled(True)
        self.tableView_radarScenes.setObjectName("tableView_radarScenes")
        self.tableView_radarScenes.horizontalHeader().setStretchLastSection(True)
        self.tableView_radarScenes.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableView_radarScenes)
        self.checkBox = QtGui.QCheckBox(Form)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_new.setText(QtGui.QApplication.translate("Form", "New", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_delete.setText(QtGui.QApplication.translate("Form", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "filter", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox.setText(QtGui.QApplication.translate("Form", "Show only my subscriptions", None, QtGui.QApplication.UnicodeUTF8))

