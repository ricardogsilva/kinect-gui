#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
'''

import numpy as np
import SimpleCV as scv
from shapely.geometry import Polygon
from mykinect import Kinect
from grid import Grid, GridWarper

class KinectNotDetectedError(Exception):
    pass

class Detector(object):

    def __init__(self, kinect_device=0, min_depth_value=200):
        #self.kinect = Kinect(kinect_device)
        self.kinect = scv.Camera() # just for testing
        try:
            im = self.kinect.getImage()
        except:
            raise KinectNotDetectedError
        self.centroids_grid = Grid(cols=im.width, lines=im.height, 
                                   depth=im.height,
                                   real_min_depth=min_depth_value)
        self.boundaries_grid = Grid(cols=im.width, lines=im.height, 
                                    depth=im.height,
                                    real_min_depth=min_depth_value)
        self.segmentation_model_depth = scv.RunningSegmentation()
        self.segmentation_model_image = scv.RunningSegmentation()
        self.image_pipeline = {
            'frame' : 0,
            'image' : None,
            'depth' : None,
        }
        self.detected = {
            'blobs' : None,
            'centroids' : None,
            'boundaries' : None,
        }
        self.previous_depth = None
        self.previous_image = None

    def capture(self, depth=False, image=False):
        self.previous_depth = self.image_pipeline['depth']
        self.previous_image = self.image_pipeline['image']
        self._clear_pipeline()
        if depth or image:
            self.image_pipeline['frame'] += 1
            if depth:
                self.image_pipeline['depth'] = self.kinect.getDepth()
                self.segmentation_model_depth.addImage(self.image_pipeline['depth'])
            if image:
                self.image_pipeline['image'] = self.kinect.getImage()
                self.segmentation_model_image.addImage(self.image_pipeline['image'])

    def _clear_pipeline(self):
        for k, v in self.image_pipeline.iteritems():
            if k != 'frame':
                self.image_pipeline[k] = None

    def _clear_detected(self):
        for k, v in self.detected.iteritems():
            self.detected[k] = None

    def _detect_with_depth(self, centroids, boundaries):
        d = self.image_pipeline['depth']
        detected = self._single_image_detection(image=d,
                                                blobs_area_filter=1500,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, centroids, boundaries = detected
        self.image_pipeline['blob_source'] = blob_image
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_image(self, centroids, boundaries):
        im = self.image_pipeline['image']
        detected = self._single_image_detection(image=im,
                                                blobs_area_filter=1500,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['blob_source'] = blob_image
        self.detected['blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_motion_depth(self, centroids, boundaries):
        diff = self.segmentation_model_depth.getSegmentedImage(whiteFG=False)
        detected = self._single_image_detection(image=diff,
                                                blobs_area_filter=1500,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['motion_depth'] = diff
        self.image_pipeline['blob_source'] = blob_image
        self.detected['blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_motion_image(self, centroids, boundaries):
        diff = self.segmentation_model_image.getSegmentedImage(whiteFG=False)
        detected = self._single_image_detection(image=diff,
                                                blobs_area_filter=1500,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['motion_image'] = diff
        self.image_pipeline['blob_source'] = blob_image
        self.detected['blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _single_image_detection(self, image, blobs_area_filter=1500,
                                get_centroids=True, get_boundaries=False):
        blobs, blob_image = self._get_blobs(image, min_area=blobs_area_filter)
        centroids = None
        boundaries = None
        if blobs is not None:
            if get_centroids:
                centroids = self._get_centroids(blobs)
                self.detected['centroids'] = centroids
            if get_boundaries:
                boundaries = self._get_boundaries(blobs)
                self.detected['boundaries'] = boundaries
        return blob_image, blobs, centroids, boundaries

    def _detect_combined(self):
        pass

    def _get_blobs(self, image, min_area=0):
        inv = image.invert()
        morphed = inv.dilate(5)
        blobs = morphed.findBlobs()
        big_blobs = None
        if blobs is not None:
            big_blobs = blobs.filter(blobs.area() > min_area)
        return big_blobs, morphed

    def _get_centroids(self, blobs, depth=None):
        '''
        Inputs:

            blobs -
            depth - A SimpleCV.Image with the depth measured by the kinect
            sensor or None. If None (the default) the returned centroids will
            have their y (depth) coordinateset to zero.
        '''

        centroids = []
        for b in blobs:
            c = self._get_kinect_coords(depth, b)
            if c is not None:
                centroids.append(c)
        if len(centroids) == 0:
            centroids = None
        return centroids

    def _get_kinect_coords(self, depth, blob):
        point = None
        x, z = blob.centroid()
        if depth is not None:
            old_image = blob.image
            blob.image = depth
            cropped = blob.crop()
            counts = self._count_pixels(cropped, remove_values=[255])
            if len(counts) > 0:
                avg_intensity = np.average(counts[:, 0], weights=counts[:, 1])
                point = int(x), int(z), int(avg_intensity)
            blob.image = old_image
        else:
            point = x, z, 0
        return point

    def _get_point_depth(self, x, z):
        x = np.round(x)
        z = np.round(z)
        try:
            depth = self.image_pipeline['depth'][x, z]
        except TypeError:
            depth = 0
        return depth

    def _count_pixels(self, image, only_useful=True, remove_values=[]):
        im = image.getNumpy()
        hist, bins = np.histogram(im, bins=range(256))
        b = list(bins)
        b.pop(0)
        counts = zip(b, hist)
        counts.sort(key=lambda item:item[1], reverse=True)
        if only_useful:
            counts = [c for c in counts if c[1] > 0]
        result = np.asarray([c for c in counts if c[0] not in remove_values])
        return result

    def _get_boundaries(self, blobs, simplify=0.5):
        boundaries = []
        for b in blobs:
            pol = Polygon(b.contour())
            s = pol.simplify(tolerance=simplify, preserve_topology=False)
            if s.type == 'Polygon' and s.exterior is not None:
                boundary = []
                for pt in s.exterior.coords:
                    x, z = pt
                    y = self._get_point_depth(x, z)
                    boundary.append((x, z, y))
                boundaries.append(boundary)
        return boundaries

    def detect(self, mode='depth', centroids=True, boundaries=False):
        '''
        Inputs:

            mode - A string with the type of detection to perform. Can be either:
                    depth: detection is done using input from the Kinect's depth
                        sensor;
                    image: detection is done using the kinect's RGB camera;
                    motion_depth: detection is done using motion detection based
                        on the depth sensor;
                    motion_image: detection is done using motion detection based
                        on the RGB camera
                    combine_depth_motion_depth:

            centroids - A boolean indicating if the centroids should be
                calculated

            boundaries - A boolean indicating if the boundaries should be
                calculated
        '''

        self._clear_detected()
        if mode == 'depth':
            self._detect_with_depth(centroids=centroids, boundaries=boundaries)
        elif mode == 'image':
            self._detect_with_image(centroids=centroids, boundaries=boundaries)
        elif mode == 'motion_depth':
            self._detect_with_motion_depth(centroids=centroids,
                                           boundaries=boundaries)
        elif mode == 'motion_image':
            self._detect_with_motion_image(centroids=centroids,
                                           boundaries=boundaries)
        elif mode == 'combine_depth_motion_depth':
            self._detect_combined()
        centroids_to_update = []
        boundaries_to_update = []
        if centroids:
            centroids_to_update = self.detected['centroids']
        if boundaries:
            for boundary in self.detected['boundaries']:
                for pt in boundary:
                    boundaries_to_update.append(pt)
        self.centroids_grid.update_grid(centroids_to_update)
        self.boundaries_grid.update_grid(boundaries_to_update)

    def get_results(self):
        results = dict()
        results.update(self.image_pipeline)
        results.update(self.detected)
        results.update({'centroids_grid' : self.centroids_grid,
                        'boundaries_grid' : self.boundaries_grid})
        return results


if __name__ == '__main__':
    d = Detector()
    while True:
        d.capture(depth=True, image=False)
        d.detect(mode='depth')

