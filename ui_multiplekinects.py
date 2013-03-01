# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'multiplekinects.ui'
#
# Created: Fri Mar  1 16:22:13 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MultipleKinectsDialog(object):
    def setupUi(self, MultipleKinectsDialog):
        MultipleKinectsDialog.setObjectName(_fromUtf8("MultipleKinectsDialog"))
        MultipleKinectsDialog.resize(641, 542)
        self.gridLayout_2 = QtGui.QGridLayout(MultipleKinectsDialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.kinects_tw = QtGui.QTabWidget(MultipleKinectsDialog)
        self.kinects_tw.setObjectName(_fromUtf8("kinects_tw"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout = QtGui.QGridLayout(self.tab)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.enable_kinect_cb = QtGui.QCheckBox(self.tab)
        self.enable_kinect_cb.setObjectName(_fromUtf8("enable_kinect_cb"))
        self.horizontalLayout.addWidget(self.enable_kinect_cb)
        self.send_osc_cb = QtGui.QCheckBox(self.tab)
        self.send_osc_cb.setObjectName(_fromUtf8("send_osc_cb"))
        self.horizontalLayout.addWidget(self.send_osc_cb)
        self.osc_settings_b = QtGui.QPushButton(self.tab)
        self.osc_settings_b.setObjectName(_fromUtf8("osc_settings_b"))
        self.horizontalLayout.addWidget(self.osc_settings_b)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(self.tab)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.detection_method_cb_b = QtGui.QComboBox(self.tab)
        self.detection_method_cb_b.setObjectName(_fromUtf8("detection_method_cb_b"))
        self.horizontalLayout_2.addWidget(self.detection_method_cb_b)
        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        self.base_image_cb_b = QtGui.QComboBox(self.tab)
        self.base_image_cb_b.setObjectName(_fromUtf8("base_image_cb_b"))
        self.horizontalLayout_2.addWidget(self.base_image_cb_b)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_3.addWidget(self.label_3)
        self.blobs_cb = QtGui.QCheckBox(self.tab)
        self.blobs_cb.setObjectName(_fromUtf8("blobs_cb"))
        self.horizontalLayout_3.addWidget(self.blobs_cb)
        self.centroids_cb = QtGui.QCheckBox(self.tab)
        self.centroids_cb.setObjectName(_fromUtf8("centroids_cb"))
        self.horizontalLayout_3.addWidget(self.centroids_cb)
        self.boundaries_cb = QtGui.QCheckBox(self.tab)
        self.boundaries_cb.setObjectName(_fromUtf8("boundaries_cb"))
        self.horizontalLayout_3.addWidget(self.boundaries_cb)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.gridLayout.addLayout(self.horizontalLayout_3, 2, 0, 1, 1)
        self.base_image_lab = QtGui.QLabel(self.tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.base_image_lab.sizePolicy().hasHeightForWidth())
        self.base_image_lab.setSizePolicy(sizePolicy)
        self.base_image_lab.setObjectName(_fromUtf8("base_image_lab"))
        self.gridLayout.addWidget(self.base_image_lab, 3, 0, 1, 1)
        self.kinects_tw.addTab(self.tab, _fromUtf8(""))
        self.gridLayout_2.addWidget(self.kinects_tw, 0, 0, 1, 1)

        self.retranslateUi(MultipleKinectsDialog)
        self.kinects_tw.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MultipleKinectsDialog)
        MultipleKinectsDialog.setTabOrder(self.kinects_tw, self.enable_kinect_cb)
        MultipleKinectsDialog.setTabOrder(self.enable_kinect_cb, self.send_osc_cb)
        MultipleKinectsDialog.setTabOrder(self.send_osc_cb, self.osc_settings_b)
        MultipleKinectsDialog.setTabOrder(self.osc_settings_b, self.detection_method_cb_b)
        MultipleKinectsDialog.setTabOrder(self.detection_method_cb_b, self.base_image_cb_b)
        MultipleKinectsDialog.setTabOrder(self.base_image_cb_b, self.centroids_cb)
        MultipleKinectsDialog.setTabOrder(self.centroids_cb, self.boundaries_cb)

    def retranslateUi(self, MultipleKinectsDialog):
        MultipleKinectsDialog.setWindowTitle(QtGui.QApplication.translate("MultipleKinectsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.enable_kinect_cb.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Enabled", None, QtGui.QApplication.UnicodeUTF8))
        self.send_osc_cb.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Send OSC", None, QtGui.QApplication.UnicodeUTF8))
        self.osc_settings_b.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "OSC settings...", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Detection method", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Base image", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Overlay", None, QtGui.QApplication.UnicodeUTF8))
        self.blobs_cb.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Raw blobs", None, QtGui.QApplication.UnicodeUTF8))
        self.centroids_cb.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Centroids", None, QtGui.QApplication.UnicodeUTF8))
        self.boundaries_cb.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "Boundaries", None, QtGui.QApplication.UnicodeUTF8))
        self.base_image_lab.setText(QtGui.QApplication.translate("MultipleKinectsDialog", "image", None, QtGui.QApplication.UnicodeUTF8))
        self.kinects_tw.setTabText(self.kinects_tw.indexOf(self.tab), QtGui.QApplication.translate("MultipleKinectsDialog", "Tab 1", None, QtGui.QApplication.UnicodeUTF8))

