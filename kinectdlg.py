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
import pygame
import numpy
import qimage2ndarray
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.prepared import prep
import OSC
import ui_kinectdlg

class OSCSender(object):

    def __init__(self, host='127.0.1.1', port=8000):
        self.client = OSC.OSCClient()
        self.client.connect((host, port))

    def send_message(self, address, *values):
        message = OSC.OSCMessage(address)
        for v in values:
            message.append(v)
        self.client.send(message)


class Detector(object):

    def __init__(self, grid_spacing=40):
        self.detector = scv.Kinect()
        im, dep = self.capture()
        self.grid = []
        for x in range(0, im.width+1, grid_spacing):
            for y in range(0, im.height+1, grid_spacing):
                self.grid.append(Point(x, y))

    def capture(self, image_type='image'):
        the_image = None
        the_depth = None
        if image_type == 'image':
            the_image = self.detector.getImage()
        elif image_type == 'depth':
            the_depth = self.detector.getDepth()
        elif image_type == 'both':
            the_image = self.detector.getImage()
            the_depth = self.detector.getDepth()
        return the_image, the_depth

    def _pre_process(self, depth, lower_threshold,
                    upper_threshold):
        one_channel = depth.getNumpyCv2()[:,:,0]
        filtered_lower = (one_channel > lower_threshold) * one_channel
        filtered_higher = (filtered_lower < upper_threshold) * filtered_lower 
        the_depth = scv.Image(filtered_higher.transpose())
        morphology_steps = 10
        dilated = the_depth.dilate(morphology_steps)
        eroded = dilated.erode(morphology_steps)
        return eroded

    def _get_qimage_from_blobs(self, blobs, detected_image):
        blobs.image = detected_image
        blobs.draw(color=scv.Color.RED, width=3)
        dl = detected_image.getDrawingLayer()
        surf = dl.renderToSurface(pygame.Surface((detected_image. width,
                                    detected_image.height)))
        arr = pygame.surfarray.array2d(surf).transpose()
        masked_array = numpy.ma.masked_equal(arr, 0)
        return qimage2ndarray.array2qimage(masked_array)

    def process_depth_detection(self, depth, 
                                lower_threshold=0, 
                                upper_threshold=255, 
                                get_centroids=True,
                                get_grid_points=True,
                                get_boundaries=True):
        centroids = None
        grid_points = None
        boundaries = None
        blobs_qim = None
        detected = self._pre_process(depth, lower_threshold, upper_threshold)
        blobs = detected.findBlobs()
        if blobs is not None:
            if get_centroids:
                centroids = self._get_centroids(blobs)
            if get_grid_points:
                grid_points = self._get_grid_points(blobs)
            if get_boundaries:
                boundaries = self._get_boundary_points(blobs)
                if len(boundaries) == 0:
                    boundaries = None
            blobs_qim = self._get_qimage_from_blobs(blobs, detected)
        return (detected, blobs_qim, centroids, grid_points, boundaries)

    def _get_centroids(self, blobs):
        return [b.centroid() for b in blobs]

    def _get_grid_points(self, blobs):
        polygons = MultiPolygon([Polygon(b.contour()) for b in blobs])
        prepared = prep(polygons)
        grid_points = filter(prepared.contains, self.grid)
        return grid_points

    def _get_boundary_points(self, blobs):
        '''
        Inputs:
            blobs - a SimpleCV.Features.Features.FeatureSet

        Returns a list of lists with shapely.Point points that are on
        a simplified boundary for each blob.
        '''

        boundaries = []
        for b in blobs:
            pol = Polygon(b.contour())
            simpler = pol.simplify(tolerance=0.5, preserve_topology=False)
            if simpler.type == 'Polygon' and simpler.exterior is not None:
                blob_boundary = []
                points = list(simpler.exterior.coords)
                for pt in list(simpler.exterior.coords):
                    blob_boundary.append(Point(pt[0], pt[1]))
                boundaries.append(blob_boundary)
        return boundaries

    def process_image_detection(self, image):
        return image


class KinectDlg(QDialog, ui_kinectdlg.Ui_KinectDialog):

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        d = Detector()
    except (TypeError,):
        box = QMessageBox()
        box.setText('Kinect not detected')
        box.exec_()
        raise SystemExit
    dlg = KinectDlg(detector=d)
    dlg.show()
    sys.exit(app.exec_())
