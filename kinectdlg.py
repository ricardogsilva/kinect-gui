#!/usr/bin/env python
#-*- coding: utf-8 -*-

'''
A Qt program to display kinect's captured images and depth and perform
detection.
'''

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qimage2ndarray
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.prepared import prep
import ui_detector
import detection
from multiplekinects import Kinect

class DetectorDlg(QDialog, ui_detector.Ui_DetectorDialog):

    def __init__(self, parent=None, detector=None):
        super(KinectDlg, self).__init__(parent)
        self.setupUi(self)
        self.min_hslider.setRange(0, 255)
        self.max_hslider.setRange(0, 255)
        self.max_hslider.setValue(190)
        self.OSC_client = None
        self.display = 'image'
        self.overlay_blobs = False
        self.overlay_centroids = False
        self.overlay_grid_points = False
        self.overlay_boundary_points = False
        self.detector = detector
        self.painter = QPainter()
        self.connect(self.image_rb, SIGNAL('toggled(bool)'),
                     self.toggle_output_image)
        self.connect(self.depth_rb, SIGNAL('toggled(bool)'),
                     self.toggle_output_image)
        self.connect(self.detection_rb, SIGNAL('toggled(bool)'),
                     self.toggle_output_image)
        self.connect(self.blobs_cb, SIGNAL('toggled(bool)'),
                     self.toggle_overlay_blobs)
        self.connect(self.centroids_cb, SIGNAL('toggled(bool)'),
                     self.toggle_overlay_centroids)
        self.connect(self.grid_cb, SIGNAL('toggled(bool)'),
                     self.toggle_overlay_grid_points)
        self.connect(self.boundaries_cb, SIGNAL('toggled(bool)'),
                     self.toggle_overlay_boundary_points)
        self.connect(self.min_hslider, SIGNAL('valueChanged(int)'),
                     self.update_slider_labels)
        self.connect(self.max_hslider, SIGNAL('valueChanged(int)'),
                     self.update_slider_labels)
        self.connect(self.server_le, SIGNAL('editingFinished()'),
                     self.update_OSC_client)
        self.detection_rb.setChecked(True)
        self.blobs_cb.setChecked(True)
        self.grid_cb.setChecked(True)
        self.update_slider_labels()
        self.startTimer(35)

    def toggle_overlay_blobs(self, toggled):
        if toggled:
            self.overlay_blobs = True
        else:
            self.overlay_blobs = False

    def toggle_overlay_centroids(self, toggled):
        if toggled:
            self.overlay_centroids = True
        else:
            self.overlay_centroids = False

    def toggle_overlay_grid_points(self, toggled):
        if toggled:
            self.overlay_grid_points = True
        else:
            self.overlay_grid_points = False

    def toggle_overlay_boundary_points(self, toggled):
        if toggled:
            self.overlay_boundary_points = True
        else:
            self.overlay_boundary_points = False

    def toggle_output_image(self, toggled):
        if self.image_rb.isChecked():
            self.display = 'image'
        elif self.depth_rb.isChecked():
            self.display = 'depth'
        elif self.detection_rb.isChecked():
            self.display = 'output'

    def timerEvent(self, event):
        image, depth = self.capture_raw()
        detected = self.update_depth_detection(depth)
        out_image, blobs, centroids, grid, boundaries = detected
        if self.display == 'image':
            to_display = (image, blobs, centroids, grid, boundaries)
        elif self.display == 'depth':
            to_display = (depth, blobs, centroids, grid, boundaries)
        elif self.display == 'output':
            to_display = (out_image, blobs, centroids, grid, boundaries)
        self.update_display(*to_display)

    def capture_raw(self):
        return self.detector.capture('both')

    def update_depth_detection(self, raw_depth):
        lower = self.min_hslider.value()
        upper = self.max_hslider.value()
        return self.detector.process_depth_detection(raw_depth, lower, upper,
                                                     self.overlay_centroids, 
                                                     self.overlay_grid_points)

    def update_display(self, output_image, blobs, centroids, 
                       points, boundaries):
        out_qim = QImage(output_image.toString(), output_image.width,
                    output_image.height, 3*output_image.width,
                    QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(out_qim)
        if self.overlay_blobs and blobs is not None:
            blobs_pix = QPixmap.fromImage(blobs)
            mask = blobs_pix.createMaskFromColor(QColor(255, 255, 255),
                                                 Qt.MaskOutColor)
            self.painter.begin(pixmap)
            self.painter.setPen(QColor(255, 0, 0))
            self.painter.drawPixmap(blobs_pix.rect(), mask, mask.rect())
            self.painter.end()
        if self.overlay_centroids and centroids is not None:
            centroid_color = QColor(0, 255, 0)
            centroid_size = 5
            brush = QBrush(centroid_color)
            self.painter.begin(pixmap)
            self.painter.setPen(centroid_color)
            self.painter.setBrush(brush)
            for c in centroids:
                pt = QPoint(int(c[0]), int(c[1]))
                self.painter.drawEllipse(pt, centroid_size, centroid_size)
            self.painter.end()
        if self.overlay_grid_points and points is not None:
            grid_color = QColor(0, 0, 255)
            grid_size = 3
            brush = QBrush(grid_color)
            self.painter.begin(pixmap)
            self.painter.setPen(grid_color)
            self.painter.setBrush(brush)
            for p in points:
                pt = QPoint(int(p.x), int(p.y))
                self.painter.drawEllipse(pt, grid_size, grid_size)
            self.painter.end()
        if self.overlay_boundary_points and boundaries is not None:
            boundary_color = QColor(255, 255, 0)
            boundary_point_size = 2
            brush = QBrush(boundary_color)
            self.painter.begin(pixmap)
            self.painter.setPen(boundary_color)
            self.painter.setBrush(brush)
            for boundary in boundaries:
                for point in boundary:
                    pt = QPoint(int(point.x), int(point.y))
                    self.painter.drawEllipse(pt, boundary_point_size,
                                             boundary_point_size)
            self.painter.end()
        self.image_label.setPixmap(pixmap)

    def update_slider_labels(self, value=None):
        self.min_label.setText(str(self.min_hslider.value()))
        self.max_label.setText(str(self.max_hslider.value()))

    def update_OSC_client(self):
        host, port = self.server_le.text().split(':')
        self.OSC_client = OSCSender(host, port)

    def send_centroids_osc_messages(self, centroids):
        base_address = '/kinect/centroids'
        for index, c in enumerate(centroids):
            address = '/'.join((base_address, index, 'xy'))
            self.osc_client.send_message(address, c[0], c[1])

def detect_kinects():
    dev_number = 0
    kinects = []
    found = True
    while found:
        try:
            k = Kinect(dev_number)
            kinects.append(k)
            dev_number += 1
        except:
            found = False
    return kinects

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        d = detection.Detector()
    except (TypeError,):
        box = QMessageBox()
        box.setText('Kinect not detected')
        box.exec_()
        raise SystemExit
    dlg = KinectDlg(detector=d)
    dlg.show()
    sys.exit(app.exec_())
