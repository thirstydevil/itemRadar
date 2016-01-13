# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\David\PycharmProjects\pythonTestBed\itemRadar\resources\ui\radarListForm.ui'
#
# Created: Wed Jan 13 22:52:44 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
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
        self.pushButton_filterTags = QtGui.QPushButton(Form)
        self.pushButton_filterTags.setObjectName("pushButton_filterTags")
        self.horizontalLayout.addWidget(self.pushButton_filterTags)
        self.pushButton_filterZone = QtGui.QPushButton(Form)
        self.pushButton_filterZone.setObjectName("pushButton_filterZone")
        self.horizontalLayout.addWidget(self.pushButton_filterZone)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.itemTableView = QtGui.QTableView(Form)
        self.itemTableView.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.itemTableView.setProperty("showDropIndicator", False)
        self.itemTableView.setAlternatingRowColors(False)
        self.itemTableView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.itemTableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.itemTableView.setObjectName("itemTableView")
        self.itemTableView.horizontalHeader().setHighlightSections(False)
        self.itemTableView.horizontalHeader().setSortIndicatorShown(True)
        self.itemTableView.horizontalHeader().setStretchLastSection(True)
        self.itemTableView.verticalHeader().setVisible(False)
        self.itemTableView.verticalHeader().setDefaultSectionSize(20)
        self.itemTableView.verticalHeader().setHighlightSections(False)
        self.itemTableView.verticalHeader().setSortIndicatorShown(True)
        self.verticalLayout.addWidget(self.itemTableView)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "filter", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_filterTags.setText(QtGui.QApplication.translate("Form", "Tags", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_filterZone.setText(QtGui.QApplication.translate("Form", "zone", None, QtGui.QApplication.UnicodeUTF8))

