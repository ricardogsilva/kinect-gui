# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'detector.ui'
#
# Created: Thu Feb 28 18:01:05 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DetectorDialog(object):
    def setupUi(self, DetectorDialog):
        DetectorDialog.setObjectName(_fromUtf8("DetectorDialog"))
        DetectorDialog.resize(635, 616)
        self.gridLayout = QtGui.QGridLayout(DetectorDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_3 = QtGui.QLabel(DetectorDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout.addWidget(self.label_3)
        self.kinects_cb = QtGui.QComboBox(DetectorDialog)
        self.kinects_cb.setObjectName(_fromUtf8("kinects_cb"))
        self.horizontalLayout.addWidget(self.kinects_cb)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(DetectorDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.base_image_cb_b = QtGui.QComboBox(DetectorDialog)
        self.base_image_cb_b.setObjectName(_fromUtf8("base_image_cb_b"))
        self.horizontalLayout_2.addWidget(self.base_image_cb_b)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label_2 = QtGui.QLabel(DetectorDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_3.addWidget(self.label_2)
        self.centroids_cb = QtGui.QCheckBox(DetectorDialog)
        self.centroids_cb.setObjectName(_fromUtf8("centroids_cb"))
        self.horizontalLayout_3.addWidget(self.centroids_cb)
        self.boudaries_cb = QtGui.QCheckBox(DetectorDialog)
        self.boudaries_cb.setObjectName(_fromUtf8("boudaries_cb"))
        self.horizontalLayout_3.addWidget(self.boudaries_cb)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.gridLayout.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)
        self.im_gv = QtGui.QGraphicsView(DetectorDialog)
        self.im_gv.setObjectName(_fromUtf8("im_gv"))
        self.gridLayout.addWidget(self.im_gv, 3, 0, 1, 1)

        self.retranslateUi(DetectorDialog)
        QtCore.QMetaObject.connectSlotsByName(DetectorDialog)

    def retranslateUi(self, DetectorDialog):
        DetectorDialog.setWindowTitle(QtGui.QApplication.translate("DetectorDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("DetectorDialog", "Kinect", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DetectorDialog", "Base image", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("DetectorDialog", "Overlay", None, QtGui.QApplication.UnicodeUTF8))
        self.centroids_cb.setText(QtGui.QApplication.translate("DetectorDialog", "Centroids", None, QtGui.QApplication.UnicodeUTF8))
        self.boudaries_cb.setText(QtGui.QApplication.translate("DetectorDialog", "Boundaries", None, QtGui.QApplication.UnicodeUTF8))

