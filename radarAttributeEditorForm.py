# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\David\PycharmProjects\pythonTestBed\itemRadar\resources\ui\radarAttributeEditorForm.ui'
#
# Created: Wed Jan 13 22:52:44 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(331, 570)
        self.mainLayout = QtGui.QVBoxLayout(Form)
        self.mainLayout.setObjectName("mainLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.name_lineEdit = QtGui.QLineEdit(Form)
        self.name_lineEdit.setObjectName("name_lineEdit")
        self.horizontalLayout.addWidget(self.name_lineEdit)
        self.mainLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_5.addWidget(self.label_3)
        self.createdOn_lineEdit = QtGui.QLineEdit(Form)
        self.createdOn_lineEdit.setReadOnly(True)
        self.createdOn_lineEdit.setObjectName("createdOn_lineEdit")
        self.horizontalLayout_5.addWidget(self.createdOn_lineEdit)
        self.mainLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_4 = QtGui.QLabel(Form)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_6.addWidget(self.label_4)
        self.createdBy_lineEdit = QtGui.QLineEdit(Form)
        self.createdBy_lineEdit.setReadOnly(True)
        self.createdBy_lineEdit.setObjectName("createdBy_lineEdit")
        self.horizontalLayout_6.addWidget(self.createdBy_lineEdit)
        self.mainLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.link_lineEdit = QtGui.QLineEdit(Form)
        self.link_lineEdit.setObjectName("link_lineEdit")
        self.horizontalLayout_2.addWidget(self.link_lineEdit)
        self.mainLayout.addLayout(self.horizontalLayout_2)
        self.pickColour_pushButton = QtGui.QPushButton(Form)
        self.pickColour_pushButton.setObjectName("pickColour_pushButton")
        self.mainLayout.addWidget(self.pickColour_pushButton)
        self.groupBox_3 = QtGui.QGroupBox(Form)
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.description_plainTextEdit = QtGui.QPlainTextEdit(self.groupBox_3)
        self.description_plainTextEdit.setObjectName("description_plainTextEdit")
        self.verticalLayout_2.addWidget(self.description_plainTextEdit)
        self.comment_toolBox = QtGui.QToolBox(self.groupBox_3)
        self.comment_toolBox.setObjectName("comment_toolBox")
        self.page_3 = QtGui.QWidget()
        self.page_3.setGeometry(QtCore.QRect(0, 0, 293, 181))
        self.page_3.setObjectName("page_3")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.page_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.pushButton_postComment = QtGui.QPushButton(self.page_3)
        self.pushButton_postComment.setObjectName("pushButton_postComment")
        self.horizontalLayout_4.addWidget(self.pushButton_postComment)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.comments_plainTextEdit = QtGui.QPlainTextEdit(self.page_3)
        self.comments_plainTextEdit.setObjectName("comments_plainTextEdit")
        self.verticalLayout_3.addWidget(self.comments_plainTextEdit)
        self.comment_toolBox.addItem(self.page_3, "")
        self.page_4 = QtGui.QWidget()
        self.page_4.setGeometry(QtCore.QRect(0, 0, 293, 165))
        self.page_4.setObjectName("page_4")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.page_4)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.commentHistory_plainTextEdit = QtGui.QPlainTextEdit(self.page_4)
        self.commentHistory_plainTextEdit.setObjectName("commentHistory_plainTextEdit")
        self.verticalLayout_4.addWidget(self.commentHistory_plainTextEdit)
        self.comment_toolBox.addItem(self.page_4, "")
        self.verticalLayout_2.addWidget(self.comment_toolBox)
        self.mainLayout.addWidget(self.groupBox_3)
        spacerItem1 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.mainLayout.addItem(spacerItem1)

        self.retranslateUi(Form)
        self.comment_toolBox.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "name", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Form", "created on", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Form", "created by", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Form", "llink", None, QtGui.QApplication.UnicodeUTF8))
        self.pickColour_pushButton.setText(QtGui.QApplication.translate("Form", "pick colour", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate("Form", "description", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_postComment.setText(QtGui.QApplication.translate("Form", "Post", None, QtGui.QApplication.UnicodeUTF8))
        self.comment_toolBox.setItemText(self.comment_toolBox.indexOf(self.page_3), QtGui.QApplication.translate("Form", "New Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.comment_toolBox.setItemText(self.comment_toolBox.indexOf(self.page_4), QtGui.QApplication.translate("Form", "Comment History", None, QtGui.QApplication.UnicodeUTF8))

