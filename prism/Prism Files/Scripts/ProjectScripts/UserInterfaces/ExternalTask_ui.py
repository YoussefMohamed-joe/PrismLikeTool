# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ExternalTask.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *  # type: ignore
from qtpy.QtGui import *  # type: ignore
from qtpy.QtWidgets import *  # type: ignore

class Ui_dlg_ExternalTask(object):
    def setupUi(self, dlg_ExternalTask):
        if not dlg_ExternalTask.objectName():
            dlg_ExternalTask.setObjectName(u"dlg_ExternalTask")
        dlg_ExternalTask.resize(708, 185)
        self.verticalLayout = QVBoxLayout(dlg_ExternalTask)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(dlg_ExternalTask)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_5 = QHBoxLayout(self.widget)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.widget_2 = QWidget(self.widget)
        self.widget_2.setObjectName(u"widget_2")
        self.verticalLayout_3 = QVBoxLayout(self.widget_2)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_3.addWidget(self.label_2)

        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")

        self.verticalLayout_3.addWidget(self.label)


        self.horizontalLayout_5.addWidget(self.widget_2)

        self.widget_4 = QWidget(self.widget)
        self.widget_4.setObjectName(u"widget_4")
        self.verticalLayout_2 = QVBoxLayout(self.widget_4)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_3 = QWidget(self.widget_4)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.w_taskName = QWidget(self.widget_3)
        self.w_taskName.setObjectName(u"w_taskName")
        self.horizontalLayout_2 = QHBoxLayout(self.w_taskName)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.e_taskName = QLineEdit(self.w_taskName)
        self.e_taskName.setObjectName(u"e_taskName")

        self.horizontalLayout_2.addWidget(self.e_taskName)


        self.horizontalLayout_3.addWidget(self.w_taskName)

        self.w_versionName = QWidget(self.widget_3)
        self.w_versionName.setObjectName(u"w_versionName")
        self.horizontalLayout_4 = QHBoxLayout(self.w_versionName)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_3 = QLabel(self.w_versionName)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.e_versionName = QLineEdit(self.w_versionName)
        self.e_versionName.setObjectName(u"e_versionName")

        self.horizontalLayout_4.addWidget(self.e_versionName)


        self.horizontalLayout_3.addWidget(self.w_versionName)


        self.verticalLayout_2.addWidget(self.widget_3)

        self.w_taskPath = QWidget(self.widget_4)
        self.w_taskPath.setObjectName(u"w_taskPath")
        self.horizontalLayout = QHBoxLayout(self.w_taskPath)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.e_taskPath = QLineEdit(self.w_taskPath)
        self.e_taskPath.setObjectName(u"e_taskPath")

        self.horizontalLayout.addWidget(self.e_taskPath)

        self.b_browseFile = QPushButton(self.w_taskPath)
        self.b_browseFile.setObjectName(u"b_browseFile")
        self.b_browseFile.setFocusPolicy(Qt.NoFocus)
        self.b_browseFile.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.b_browseFile)

        self.b_browseFolder = QPushButton(self.w_taskPath)
        self.b_browseFolder.setObjectName(u"b_browseFolder")
        self.b_browseFolder.setFocusPolicy(Qt.NoFocus)
        self.b_browseFolder.setContextMenuPolicy(Qt.CustomContextMenu)

        self.horizontalLayout.addWidget(self.b_browseFolder)


        self.verticalLayout_2.addWidget(self.w_taskPath)


        self.horizontalLayout_5.addWidget(self.widget_4)


        self.verticalLayout.addWidget(self.widget)

        self.widget_5 = QWidget(dlg_ExternalTask)
        self.widget_5.setObjectName(u"widget_5")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_5)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_4 = QLabel(self.widget_5)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_6.addWidget(self.label_4)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)

        self.rb_copy = QRadioButton(self.widget_5)
        self.rb_copy.setObjectName(u"rb_copy")
        self.rb_copy.setChecked(True)

        self.horizontalLayout_6.addWidget(self.rb_copy)

        self.rb_move = QRadioButton(self.widget_5)
        self.rb_move.setObjectName(u"rb_move")

        self.horizontalLayout_6.addWidget(self.rb_move)

        self.rb_link = QRadioButton(self.widget_5)
        self.rb_link.setObjectName(u"rb_link")

        self.horizontalLayout_6.addWidget(self.rb_link)


        self.verticalLayout.addWidget(self.widget_5)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(dlg_ExternalTask)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(dlg_ExternalTask)
        self.buttonBox.accepted.connect(dlg_ExternalTask.accept)
        self.buttonBox.rejected.connect(dlg_ExternalTask.reject)

        QMetaObject.connectSlotsByName(dlg_ExternalTask)
    # setupUi

    def retranslateUi(self, dlg_ExternalTask):
        dlg_ExternalTask.setWindowTitle(QCoreApplication.translate("dlg_ExternalTask", u"Add external media", None))
        self.label_2.setText(QCoreApplication.translate("dlg_ExternalTask", u"Identifier:", None))
        self.label.setText(QCoreApplication.translate("dlg_ExternalTask", u"External path:", None))
        self.label_3.setText(QCoreApplication.translate("dlg_ExternalTask", u"Versionname:", None))
        self.b_browseFile.setText(QCoreApplication.translate("dlg_ExternalTask", u"...(file)", None))
        self.b_browseFolder.setText(QCoreApplication.translate("dlg_ExternalTask", u"...(folder)", None))
        self.label_4.setText(QCoreApplication.translate("dlg_ExternalTask", u"Action:", None))
        self.rb_copy.setText(QCoreApplication.translate("dlg_ExternalTask", u"Copy", None))
        self.rb_move.setText(QCoreApplication.translate("dlg_ExternalTask", u"Move", None))
        self.rb_link.setText(QCoreApplication.translate("dlg_ExternalTask", u"Link", None))
    # retranslateUi

