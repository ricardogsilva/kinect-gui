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
import ui_oscsettings
import detection
from osccommunicator import OSCCommunicator

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class OSCSettingsDlg(QDialog, ui_oscsettings.Ui_OSCSettingsDialog):

    def __init__(self, parent=None):
        super(OSCSettingsDlg, self).__init__(parent)
        self.setupUi(self)


class MultipleKinectsDlg(QDialog, ui_multiplekinects.Ui_MultipleKinectsDialog):

    DETECTION_METHODS = {
        'depth' : ['depth', 'blob_source'],
        'image' : ['image', 'blob_source', 'centroids_grid_xy',
                   'centroids_grid_xz', 'boundaries_grid_xy',
                   'boundaries_grid_xz'],
        'motion_depth' : ['depth', 'motion_depth', 'blob_source'],
        'motion_image' :['image', 'motion_image', 'blob_source'],
    }

    def __init__(self, kinects, parent=None):
        super(MultipleKinectsDlg, self).__init__(parent)
        self.setupUi(self)
        self.painter = QPainter()
        self.kinects = dict()
        tab_idx = self.kinects_tw.currentIndex()
        first_page = self.kinects_tw.widget(tab_idx)
        self.tabs = [first_page]
        self.current_tab = tab_idx
        self.connect(self.kinects_tw, SIGNAL('currentChanged()'),
                        self.toggle_current_tab)
        for index, k in enumerate(kinects):
            self.kinects[index] = dict()
            if index  != 0:
                t = self.add_tab('Kinect %i' % k.device_number, index)
                self.tabs.append(t)
                self.kinects[index]['widgets'] = {
                    'enable_kinect_cb' : t.findChildren(QCheckBox, 
                                                        QRegExp('enable_kinect_cb.*'))[0],
                    'send_osc_cb' : t.findChildren(QCheckBox,
                                                    QRegExp('send_osc_cb.*'))[0],
                    'OSC_settings_b' : t.findChildren(QPushButton,
                                                      QRegExp('osc_settings_b.*'))[0],
                    'detection_method_cb_b' : t.findChildren(QComboBox,
                                                             QRegExp('detection_method_cb_b.*'))[0],
                    'base_image_cb_b' : t.findChildren(QComboBox,
                                                       QRegExp('base_image_cb_b.*'))[0],
                    'overlay_blobs_cb' : t.findChildren(QCheckBox,
                                                        QRegExp('blobs_cb.*'))[0],
                    'overlay_centroids_cb' : t.findChildren(QCheckBox,
                                                            QRegExp('centroids_cb.*'))[0],
                    'overlay_boundaries_cb' : t.findChildren(QCheckBox,
                                                             QRegExp('boundaries_cb.*'))[0],
                    'base_image_lab' : t.findChildren(QLabel, QRegExp('base_image_lab.*'))[0],
                }
            else:
                self.kinects[index]['widgets'] = {
                    'enable_kinect_cb' : self.enable_kinect_cb,
                    'send_osc_cb' : self.send_osc_cb,
                    'OSC_settings_b' : self.osc_settings_b,
                    'detection_method_cb_b' : self.detection_method_cb_b,
                    'base_image_cb_b' : self.base_image_cb_b,
                    'overlay_blobs_cb' : self.blobs_cb,
                    'overlay_centroids_cb' : self.centroids_cb,
                    'overlay_boundaries_cb' : self.boundaries_cb,
                    'base_image_lab' : self.base_image_lab,
                }
        self.kinects_tw.setTabText(tab_idx, 'Kinect %i' % tab_idx)

        for key, value in self.kinects.iteritems():
            value['widgets']['base_image_lab'].setFixedSize(640, 480)
            value['widgets']['detection_method_cb_b'].insertItems(0, sorted(self.DETECTION_METHODS.keys()))
            self.connect(value['widgets']['enable_kinect_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_enable_kinect)
            self.connect(value['widgets']['send_osc_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_send_osc)
            self.connect(value['widgets']['detection_method_cb_b'],
                         SIGNAL('currentIndexChanged(const QString&)'),
                         self.toggle_detection_method)
            self.connect(value['widgets']['base_image_cb_b'],
                         SIGNAL('currentIndexChanged(const QString&)'),
                         self.toggle_base_image)
            self.connect(value['widgets']['overlay_blobs_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_overlay_blobs)
            self.connect(value['widgets']['overlay_centroids_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_overlay_centroids)
            self.connect(value['widgets']['overlay_boundaries_cb'], SIGNAL('toggled(bool)'),
                        self.toggle_overlay_boundaries)
            self.connect(value['widgets']['OSC_settings_b'], SIGNAL('clicked()'),
                        self.set_osc_settings)
        self.load_settings(kinects)
        self.restore_gui()
        #self.kinects[0]['widgets']['enable_kinect_cb'].setChecked(True)
        self.startTimer(35)

    def load_settings(self, kinects):
        the_settings = dict()
        s = QSettings()
        for i, kinect in enumerate(kinects):
            default_detect_meth = self.DETECTION_METHODS.keys()[0]
            default_base_im = self.DETECTION_METHODS[default_detect_meth][0]
            osc_client_ip = s.value('kinect%i/osc_server_ip' % i, 
                                    QVariant('127.0.1.1')).toString()
            osc_client_port = s.value('kinect%i/osc_server_port',
                                      QVariant(5000)).toInt()[0]
            self.kinects[i].update({
                'detector' : kinect,
                'status' : s.value('kinect%i/status' % i, QVariant(False)).toBool(),
                'send_osc' : s.value('kinect%i/send_osc' % i, QVariant(False)).toBool(),
                'send_osc_centroids_grid' : s.value('kinect%i/send_osc_centroids_grid' % i, QVariant(False)).toBool(),
                'send_osc_boundaries_grid' : s.value('kinect%i/send_osc_boundaries_grid' % i, QVariant(False)).toBool(),
                'detection_method' : s.value('kinect%i/detection_method' % i,
                                             QVariant(default_detect_meth)).toString(),
                'base_image' : s.value('kinect%i/base_image' % i,
                                       QVariant(default_base_im)).toString(),
                'overlay_blobs' : s.value('kinect%i/overlay_blobs' % i, QVariant(False)).toBool(),
                'overlay_centroids' : s.value('kinect%i/overlay_centroids' % i, QVariant(False)).toBool(),
                'overlay_boundaries' : s.value('kinect%i/overlay_boundaries' % i, QVariant(False)).toBool(),
                'osc_server_ip' : osc_client_ip,
                'osc_server_port' : osc_client_port,
                'osc_communicator' : OSCCommunicator(client_ip=osc_client_ip, client_port=osc_client_port),
            })

    def restore_gui(self):
        for index, ks in self.kinects.iteritems():
            gui = ks['widgets']
            settings_base_image = ks['base_image']
            gui['enable_kinect_cb'].setChecked(ks['status'])
            gui['send_osc_cb'].setChecked(ks['send_osc'])
            detect_meth_index = self._find_cb_b_index(gui['detection_method_cb_b'], ks['detection_method'])
            gui['detection_method_cb_b'].setCurrentIndex(detect_meth_index)

            base_im_index = self._find_cb_b_index(gui['base_image_cb_b'], settings_base_image)
            gui['base_image_cb_b'].setCurrentIndex(base_im_index)

            gui['overlay_blobs_cb'].setChecked(ks['overlay_blobs'])
            gui['overlay_centroids_cb'].setChecked(ks['overlay_centroids'])
            gui['overlay_boundaries_cb'].setChecked(ks['overlay_boundaries'])

    def toggle_current_tab(self):
        self.current_tab = self.kinects_tw.currentIndex()

    def _find_cb_b_index(self, cb, text):
        the_index = None
        for i in range(cb.count()):
            t = cb.itemText(i)
            if str(t) == str(text):
                the_index = i
        return the_index

    def closeEvent(self, event):
        settings = QSettings()
        for index, ks in self.kinects.iteritems():
            settings.setValue('kinect%i/status' % index, QVariant(ks['status']))
            settings.setValue('kinect%i/send_osc' % index, QVariant(ks['send_osc']))
            settings.setValue('kinect%i/send_osc_centroids_grid' % index, QVariant(ks['send_osc_centroids_grid']))
            settings.setValue('kinect%i/send_osc_boundaries_grid' % index, QVariant(ks['send_osc_boundaries_grid']))
            settings.setValue('kinect%i/detection_method' % index,
                              QVariant(ks['detection_method']))
            settings.setValue('kinect%i/base_image' % index,
                              QVariant(ks['base_image']))
            settings.setValue('kinect%i/overlay_blobs' % index,
                              QVariant(ks['overlay_blobs']))
            settings.setValue('kinect%i/overlay_centroids' % index,
                              QVariant(ks['overlay_centroids']))
            settings.setValue('kinect%i/overlay_boundaries' % index,
                              QVariant(ks['overlay_boundaries']))
            settings.setValue('kinect%i/osc_server_ip' % index,
                              QVariant(ks['osc_server_ip']))
            settings.setValue('kinect%i/osc_server_port' % index,
                              QVariant(ks['osc_server_port']))

    def set_osc_settings(self):
        index, s = self._get_index_settings()
        dialog = OSCSettingsDlg(self)
        dialog.osc_server_ip_le.setText(s['osc_server_ip'])
        dialog.osc_server_port_le.setText(s['osc_server_port'])
        if dialog.exec_():
            client_ip = dialog.osc_server_ip_le.text()
            client_port = dialog.osc_server_port_le.text()
            s['osc_server_ip'] = client_ip
            s['osc_server_port'] = client_port
            settings['osc_communicator'] = OSCCommunicator(
                client_ip=client_ip,
                client_port=client_port
            )

    def toggle_enable_kinect(self, toggled):
        index, settings = self._get_index_settings()
        settings['status'] = settings['widgets']['enable_kinect_cb'].isChecked()

    def toggle_send_osc(self, toggled):
        index, settings = self._get_index_settings()
        settings['send_osc'] = settings['widgets']['send_osc_cb'].isChecked()

    def _get_index_settings(self):
        index = self.kinects_tw.currentIndex()
        settings = self.kinects.get(index)
        return index, settings

    def toggle_detection_method(self, detection_method):
        for index, ks in self.kinects.iteritems():
            det_meth = str(ks['widgets']['detection_method_cb_b'].currentText())
            base_images = self.DETECTION_METHODS.get(det_meth)
            ks['detection_method'] = det_meth
            ks['widgets']['base_image_cb_b'].clear()
            ks['widgets']['base_image_cb_b'].insertItems(0, base_images)

    def toggle_base_image(self, base_image):
        for index, ks in self.kinects.iteritems():
            ks['base_image'] = str(ks['widgets']['base_image_cb_b'].currentText())

    def toggle_overlay_blobs(self, toggled):
        index, settings = self._get_index_settings()
        settings['overlay_blobs'] = settings['widgets']['overlay_blobs_cb'].isChecked()

    def toggle_overlay_centroids(self, toggled):
        index, settings = self._get_index_settings()
        settings['overlay_centroids'] = settings['widgets']['overlay_centroids_cb'].isChecked()

    def toggle_overlay_boundaries(self, toggled):
        index, settings = self._get_index_settings()
        settings['overlay_boundaries'] = settings['widgets']['overlay_boundaries_cb'].isChecked()

    def timerEvent(self, event):
        current_page = self.kinects_tw.currentIndex()
        for index, ks in self.kinects.iteritems():
            if ks['status']:
                kinect = ks['detector']
                #kinect.capture(image=True, depth=True)
                kinect.capture(image=True) # just for testing
                process_centroids = False
                process_boundaries = False
                if ks['overlay_centroids'] or ks['base_image'] in ('centroids_grid_xy',
                        'centroids_grid_xz'):
                    process_centroids = True
                if ks['overlay_boundaries'] or ks['base_image'] in \
                        ('boundaries_grid_xy', 'boundaries_grid_xz'):
                    process_boundaries = True
                kinect.detect(mode=ks['detection_method'], 
                              centroids=process_centroids,
                              boundaries=process_boundaries)
                results = kinect.get_results()
                if ks['send_osc']:
                    kinect.send_osc_messages(ks['osc_communicator'])
                if index == current_page:
                    self.update_display(ks, results)

    def update_display(self, settings, results):
        to_display = results[str(settings['base_image'])]
        the_label = settings['widgets']['base_image_lab']
        if to_display is not None:
            pixmap = self._update_base_image(to_display)
            if settings['overlay_blobs'] and results['blobs'] is not None:
                self._draw_blobs(results['blobs'], pixmap)
            if settings['overlay_centroids']:
                self._draw_centroids(results['centroids'], pixmap)
            if settings['overlay_boundaries']:
                self._draw_boundaries(results['boundaries'], pixmap)
            the_label.setPixmap(pixmap)

    def _update_base_image(self, image):
        qim = QImage(image.toString(), image.width, image.height, 
                     3*image.width, QImage.Format_RGB888)
        return QPixmap.fromImage(qim)

    def _draw_blobs(self, blobs, pixmap, color=QColor(255, 0, 0, 100)):
        brush = QBrush(color)
        self.painter.begin(pixmap)
        self.painter.setPen(color)
        self.painter.setBrush(brush)
        for b in blobs:
            pol = QPolygon([QPoint(pt[0], pt[1]) for pt in b.contour()])
            self.painter.drawPolygon(pol)
        self.painter.end()

    def _draw_centroids(self, centroids, pixmap,
                        color=QColor(0, 255, 0, 100),
                        size=5):
        brush = QBrush(color)
        self.painter.begin(pixmap)
        self.painter.setPen(color)
        self.painter.setBrush(brush)
        for c in centroids:
            self.painter.drawEllipse(QPoint(c[0], c[1]), size, size)
        self.painter.end()

    def _draw_boundaries(self, boundaries, pixmap,
                         color=QColor(0, 0, 255, 100),
                         size=3):
        brush = QBrush(color)
        self.painter.begin(pixmap)
        self.painter.setPen(color)
        self.painter.setBrush(brush)
        for b in boundaries:
            for pt in b:
                self.painter.drawEllipse(QPoint(pt[0], pt[1]), size, size)
        self.painter.end()

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
        blobs_cb = QCheckBox(self.tab)
        blobs_cb.setObjectName(_fromUtf8("blobs_cb_%s" % index))
        horizontalLayout_2.addWidget(blobs_cb)
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
        blobs_cb.setText(QApplication.translate("MultipleKinectsDialog", "Raw blobs", None, QApplication.UnicodeUTF8))
        centroids_cb.setText(QApplication.translate("MultipleKinectsDialog", "Centroids", None, QApplication.UnicodeUTF8))
        boundaries_cb.setText(QApplication.translate("MultipleKinectsDialog", "Boundaries", None, QApplication.UnicodeUTF8))
        return t


class DummyKinect(object):

    def __init__(self, device_number=0):
        self.device_number = device_number


def test_data():
    k0 = detection.Detector()
    k0.device_number = 0
    k1 = DummyKinect(1)
    return [k0, k1]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setOrganizationName('rixilva')
    app.setOrganizationDomain('rixilva.pt')
    app.setApplicationName('Kinect Detection')
    #kinects = detection.Detector.detect_kinects()
    kinects = test_data() # just for testing
    if len(kinects) == 0:
        box = QMessageBox()
        box.setText('No Kinects have been detected.')
        box.exec_()
        raise SystemExit
    dlg = MultipleKinectsDlg(kinects=kinects)
    dlg.show()
    sys.exit(app.exec_())
