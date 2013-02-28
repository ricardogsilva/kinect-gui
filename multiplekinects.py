#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
A Qt program to display kinect's captured images and depth and perform
detection.
'''

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import SimpleCV as scv
import qimage2ndarray
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.prepared import prep
import ui_multiplekinects
import detection

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class MultipleKinectsDlg(QDialog, ui_multiplekinects.Ui_MultipleKinectsDialog):

    def __init__(self, kinects, parent=None):
        super(MultipleKinectsDlg, self).__init__(parent)
        self.setupUi(self)
        self.kinects = dict()
        DETECTION_METHODS = ['depth', 'image', 'motion depth','motion image']
        BASE_IMAGES = ['depth', 'image', 'blob_source', 'motion_depth',
                       'motion_image']
        tab_idx = self.kinects_tw.currentIndex()
        first_page = self.kinects_tw.widget(tab_idx)
        self.tabs = [first_page]
        for index, k in enumerate(kinects):
            self.kinects[index] = {
                'detector' : k,
                'status' : False, 
                'detection_method' : DETECTION_METHODS[0],
                'base_image' : None,
                'overlay_centroids' : False,
                'overlay_boundaries' : False,
            }
            if index  != 0:
                t = self.add_tab('Kinect %i' % k.device_number, index)
                self.tabs.append(t)
                self.kinects[index]['widgets'] = {
                    'enable_kinect_cb' : t.findChildren(QCheckBox, 
                                                        QRegExp('enable_kinect_cb.*'))[0],
                    'send_OSC_cb' : t.findChildren(QCheckBox,
                                                    QRegExp('send_osc_cb.*'))[0],
                    'OSC_settings_b' : t.findChildren(QPushButton,
                                                      QRegExp('osc_settings_b.*'))[0],
                    'detection_method_cb_b' : t.findChildren(QComboBox,
                                                             QRegExp('detection_method_cb_b.*'))[0],
                    'base_image_cb_b' : t.findChildren(QComboBox,
                                                       QRegExp('base_image_cb_b.*'))[0],
                    'overlay_centroids_cb' : t.findChildren(QCheckBox,
                                                            QRegExp('centroids_cb.*'))[0],
                    'overlay_boundaries_cb' : t.findChildren(QCheckBox,
                                                             QRegExp('boundaries_cb.*'))[0],
                    'base_image_lab' : t.findChildren(QLabel, QRegExp('base_image_lab.*'))[0],
                }
            else:
                self.kinects[index]['widgets'] = {
                    'enable_kinect_cb' : self.enable_kinect_cb,
                    'send_OSC_cb' : self.send_osc_cb,
                    'OSC_settings_b' : self.osc_settings_b,
                    'detection_method_cb_b' : self.detection_method_cb_b,
                    'base_image_cb_b' : self.base_image_cb_b,
                    'overlay_centroids_cb' : self.centroids_cb,
                    'overlay_boundaries_cb' : self.boundaries_cb,
                    'base_image_lab' : self.base_image_lab,
                }
        self.kinects_tw.setTabText(tab_idx, 
                                   'Kinect %i' % self.kinects[0]['detector'].device_number)

        for key, value in self.kinects.iteritems():
            value['widgets']['detection_method_cb_b'].insertItems(0, DETECTION_METHODS)
            value['widgets']['base_image_cb_b'].insertItems(0, BASE_IMAGES)
            self.connect(value['widgets']['enable_kinect_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_enable_kinect)
            self.connect(value['widgets']['detection_method_cb_b'],
                         SIGNAL('currentIndexChanged(const QString&)'),
                         self.toggle_detection_method)
            self.connect(value['widgets']['base_image_cb_b'],
                         SIGNAL('currentIndexChanged(const QString&)'),
                         self.toggle_base_image)
            self.connect(value['widgets']['overlay_centroids_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_overlay_centroids)
            self.connect(value['widgets']['overlay_boundaries_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_overlay_boundaries)

        self.kinects[0]['widgets']['enable_kinect_cb'].setChecked(True)

        self.startTimer(35)

    def toggle_enable_kinect(self, toggled):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        settings['status'] = settings['widgets']['enable_kinect_cb'].isChecked()

    def toggle_detection_method(self, detection_method):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        settings['detection_method'] = detection_method

    def toggle_base_image(self, base_image):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        settings['base_image'] = base_image

    def toggle_overlay_centroids(self, toggled):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        settings['overlay_centroids'] = settings['widgets']['overlay_centroids_cb'].isChecked()

    def toggle_overlay_boundaries(self, toggled):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        settings['overlay_boundaries'] = settings['widgets']['overlay_boundaries_cb'].isChecked()

    def timerEvent(self, event):
        for index, values in self.kinects.iteritems():
            if values['status']:
                kinect = values['detector']
                kinect.capture(image=True)
                if values['detection_method'] == 'depth':
                    pass
                elif values['detection_method'] == 'image':
                    kinect.detect(mode='image')
                kinect.detect(mode='image', 
                              centroids=values['overlay_centroids'],
                              boundaries=values['overlay_boundaries'])
                results = kinect.get_results()
                self.update_display(values, results)

    def update_display(self, kinect_settings, results):
        to_display = None
        if kinect_settings['base_image'] == 'image':
            to_display = results['image']
        elif kinect_settings['base_image'] == 'blob_source':
            to_display = results['blob_source']
        if to_display is not None:
            qim = QImage(to_display.toString(), to_display.width,
                         to_display.height, 3*to_display.width,
                         QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qim)
            kinect_settings['widgets']['base_image_lab'].setPixmap(pixmap)




    def add_tab(self, name, index):
        t = QWidget()
        t.setObjectName(_fromUtf8('%s_tab' % name))
        gridLayout = QGridLayout(t)
        gridLayout.setObjectName(_fromUtf8("gridLayout_%s" % index))
        first_row_layout = QHBoxLayout()
        first_row_layout.setObjectName(_fromUtf8("first_row_layout_%s" % index))
        enable_kinect_cb = QCheckBox(t)
        enable_kinect_cb.setObjectName(_fromUtf8("enable_kinect_cb_%s" % index))
        first_row_layout.addWidget(enable_kinect_cb)
        send_osc_cb = QCheckBox(t)
        send_osc_cb.setObjectName(_fromUtf8("send_osc_cb_%s" % index))
        first_row_layout.addWidget(send_osc_cb)
        osc_settings_b = QPushButton(t)
        osc_settings_b.setObjectName(_fromUtf8("osc_settings_b_%s" % index))
        first_row_layout.addWidget(osc_settings_b)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        first_row_layout.addItem(spacerItem)
        gridLayout.addLayout(first_row_layout, 0, 0, 1, 1)
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setObjectName(_fromUtf8("horizontalLayout_%s" % index))
        label = QLabel(t)
        label.setObjectName(_fromUtf8("label_%s" % index))
        horizontalLayout.addWidget(label)
        detection_method_cb_b = QComboBox(t)
        detection_method_cb_b.setObjectName(_fromUtf8(
                                            "detection_method_cb_b_%s" % index))
        horizontalLayout.addWidget(detection_method_cb_b)
        label_2 = QLabel(t)
        label_2.setObjectName(_fromUtf8("label_2_%s" % index))
        horizontalLayout.addWidget(label_2)
        base_image_cb_b = QComboBox(t)
        base_image_cb_b.setObjectName(_fromUtf8("base_image_cb_b_%s" % index))
        horizontalLayout.addWidget(base_image_cb_b)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout.addItem(spacerItem1)
        gridLayout.addLayout(horizontalLayout, 1, 0, 1, 1)
        horizontalLayout_2 = QHBoxLayout()
        horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2_%s" %
            index))
        label_3 = QLabel(t)
        label_3.setObjectName(_fromUtf8("label_3_%s" % index))
        horizontalLayout_2.addWidget(label_3)
        centroids_cb = QCheckBox(t)
        centroids_cb.setObjectName(_fromUtf8("centroids_cb_%s" % index))
        horizontalLayout_2.addWidget(centroids_cb)
        boundaries_cb = QCheckBox(t)
        boundaries_cb.setObjectName(_fromUtf8("boundaries_cb_%s" % index))
        horizontalLayout_2.addWidget(boundaries_cb)
        spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem2)
        gridLayout.addLayout(horizontalLayout_2, 2, 0, 1, 1)

        base_image_lab = QLabel(self.tab)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.base_image_lab.sizePolicy().hasHeightForWidth())
        base_image_lab.setSizePolicy(sizePolicy)
        base_image_lab.setObjectName(_fromUtf8("base_image_lab_%s" % index))
        gridLayout.addWidget(base_image_lab, 3, 0, 1, 1)
        self.kinects_tw.addTab(t, name)

        enable_kinect_cb.setText(QApplication.translate("MultipleKinectsDialog", "Enabled", None, QApplication.UnicodeUTF8))
        send_osc_cb.setText(QApplication.translate("MultipleKinectsDialog", "Send OSC", None, QApplication.UnicodeUTF8))
        osc_settings_b.setText(QApplication.translate("MultipleKinectsDialog", "OSC settings...", None, QApplication.UnicodeUTF8))
        label.setText(QApplication.translate("MultipleKinectsDialog", "Detection method", None, QApplication.UnicodeUTF8))
        label_2.setText(QApplication.translate("MultipleKinectsDialog", "Base image", None, QApplication.UnicodeUTF8))
        label_3.setText(QApplication.translate("MultipleKinectsDialog", "Overlay", None, QApplication.UnicodeUTF8))
        centroids_cb.setText(QApplication.translate("MultipleKinectsDialog", "Centroids", None, QApplication.UnicodeUTF8))
        boundaries_cb.setText(QApplication.translate("MultipleKinectsDialog", "Boundaries", None, QApplication.UnicodeUTF8))
        return t


class DummyKinect(object):

    def __init__(self, device_number=0):
        self.device_number = device_number


def detect_kinects():
    dev_number = 0
    kinects = []
    found = True
    while found:
        try:
            k = detection.Detector(dev_number)
            kinects.append(k)
            dev_number += 1
        except:
            found = False
    return kinects

def test_data():
    k0 = detection.Detector()
    k0.device_number = 0
    k1 = DummyKinect(1)
    k2 = DummyKinect(2)
    return [k0, k1, k2]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    #kinects = detect_kinects()
    kinects = test_data() # just for testing
    if len(kinects) == 0:
        box = QMessageBox()
        box.setText('No Kinects have been detected.')
        box.exec_()
        raise SystemExit
    dlg = MultipleKinectsDlg(kinects=kinects)
    dlg.show()
    sys.exit(app.exec_())
