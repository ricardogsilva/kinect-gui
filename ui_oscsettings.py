# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'oscsettings.ui'
#
# Created: Sun Mar  3 16:12:25 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_OSCSettingsDialog(object):
    def setupUi(self, OSCSettingsDialog):
        OSCSettingsDialog.setObjectName(_fromUtf8("OSCSettingsDialog"))
        OSCSettingsDialog.resize(508, 151)
        self.verticalLayout = QtGui.QVBoxLayout(OSCSettingsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(OSCSettingsDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.osc_server_ip_le = QtGui.QLineEdit(OSCSettingsDialog)
        self.osc_server_ip_le.setObjectName(_fromUtf8("osc_server_ip_le"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.osc_server_ip_le)
        self.label_2 = QtGui.QLabel(OSCSettingsDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_2)
        self.osc_server_port_le = QtGui.QLineEdit(OSCSettingsDialog)
        self.osc_server_port_le.setObjectName(_fromUtf8("osc_server_port_le"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.osc_server_port_le)
        self.label_3 = QtGui.QLabel(OSCSettingsDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_3)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.send_centroids_grid_cb = QtGui.QCheckBox(OSCSettingsDialog)
        self.send_centroids_grid_cb.setObjectName(_fromUtf8("send_centroids_grid_cb"))
        self.horizontalLayout.addWidget(self.send_centroids_grid_cb)
        self.send_boundaries_grid_cb = QtGui.QCheckBox(OSCSettingsDialog)
        self.send_boundaries_grid_cb.setObjectName(_fromUtf8("send_boundaries_grid_cb"))
        self.horizontalLayout.addWidget(self.send_boundaries_grid_cb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.formLayout.setLayout(2, QtGui.QFormLayout.FieldRole, self.horizontalLayout)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.buttonBox = QtGui.QDialogButtonBox(OSCSettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout_4.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.retranslateUi(OSCSettingsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), OSCSettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), OSCSettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(OSCSettingsDialog)

    def retranslateUi(self, OSCSettingsDialog):
        OSCSettingsDialog.setWindowTitle(QtGui.QApplication.translate("OSCSettingsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("OSCSettingsDialog", "Server IP", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("OSCSettingsDialog", "Port", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("OSCSettingsDialog", "OSC messages", None, QtGui.QApplication.UnicodeUTF8))
        self.send_centroids_grid_cb.setText(QtGui.QApplication.translate("OSCSettingsDialog", "centroids grid", None, QtGui.QApplication.UnicodeUTF8))
        self.send_boundaries_grid_cb.setText(QtGui.QApplication.translate("OSCSettingsDialog", "boundaries grid", None, QtGui.QApplication.UnicodeUTF8))

