#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
'''

import numpy as np
import scipy.spatial as spatial
import SimpleCV as scv
from shapely.geometry import Polygon
from mykinect import Kinect
from grid import Grid, GridWarper
from osccommunicator import OSCCommunicator

class ActorManager(object):

    def __init__(self):
        self.points = []

    def update_points(self, coordinates, distance_threshold=100):
        num_points_changes = len(coordinates) - len(self.points)
        if num_points_changes > 0:
            # there are new points to add
            if len(self.points) == 0:
                # all the points are new, add them
                self.points = [Actor(c) for c in coordinates]
            else:
                # first, match the old points
                matches = self._find_nearest_coordinate(coordinates)
                used_coordinates = []
                for pt, value in matches.iteritems():
                    coords, dist = value
                    used_coordinates.append(coords)
                    if dist is not None and dist < distance_threshold:
                        pt.moved(coords)
                # now add the new points
                unused_coordinates = [c for c in coordinates if c not in \
                                      used_coordinates]
                for c in unused_coordinates:
                    self.points.append(Actor(c))
        elif num_points_changes < 0:
            # remove the points that are gone
            if num_points_changes == (self.points * -1):
                # all the points are gone
                self.points = []
            else:
                coord_matches = self._find_nearest_point(coordinates)
                used_points = []
                for coord, value in coord_matches.iteritems():
                    point, dist = value
                    used_points.append(point)
                    point.moved(coord)
                self.points = used_points
        else:
            #existing points are the same, update them
            matches = self._find_nearest_point(coordinates)
            for c, values in matches.iteritems():
                pt, dist = values
                if dist < distance_threshold:
                    pt.moved(c)

    def _find_nearest_point(self, coordinates):
        '''
        Find the nearest point to each coordinate.

        Inputs:

            coordinates - A list of (x, z, y) tuples with the coordinates to match.

        Returns: A dictionary with each input coordinate as key and a tuple
            (point, distance) with the instance's point that is nearest to the
            coordinate and the respective distance.
        '''

        matches = dict()
        for c in coordinates:
            nearest_point = None
            the_dist = None
            for p in self.points:
                dist = spatial.distance.euclidean(p.location, np.asarray(c))
                if the_dist is None:
                    the_dist = dist
                else:
                    the_dist = min(the_dist, dist)
                if the_dist == dist:
                    nearest_point = p
            matches[c] = (nearest_point, the_dist)
        return matches

    def _find_nearest_coordinate(self, coordinates):
        '''
        Find the nearest coordinate to each point.

        Inputs:

            coordinates - A list of (x, z, y) tuples with the coordinates.

        Returns: A dictionary with points as keys and a tuple with the 
            nearest coordinate and the respective distance.
        '''

        matches = dict()
        for p in self.points:
            nearest_coord = None
            the_dist = None
            for c in coordinates:
                dist = spatial.distance.euclidean(p.location, np.asarray(c))
                if the_dist is None:
                    the_dist = dist
                else:
                    the_dist = min(the_dist, dist)
                if the_dist == dist:
                    nearest_coord = c
            matches[p] = (nearest_coord, the_dist)
        return matches

class Actor(object):

    def __init__(self, coords, color=None):
        if color is None:
            self.color = scv.Color().getRandom()
        else:
            self.color = color
        self.location = np.asarray(coords)
        self.velocity = np.asarray([0, 0, 0])
        self.acceleration = np.asarray([0, 0, 0])
        self.direction = None
        self.acceleration = 0

    def moved(self, new_coords):
        new_coords = np.asarray(new_coords)
        vel = new_coords - self.location
        accel = vel - self.velocity
        self.acceleration = accel
        self.velocity = vel
        self.location = new_coords


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

    @classmethod
    def detect_kinects(cls):
        dev_number = 0
        kinects = []
        found = True
        while found:
            try:
                k = Detector(dev_number)
                kinects.append(k)
                dev_number += 1
            except:
                found = False
        return kinects

    def _add_grids_to_image_pipeline(self):
        c_xy_im = self.centroids_grid.get_image(grid_type='xy')
        c_xz_im = self.centroids_grid.get_image(grid_type='xz')
        b_xy_im = self.boundaries_grid.get_image(grid_type='xy')
        b_xz_im = self.boundaries_grid.get_image(grid_type='xz')
        self.image_pipeline['centroids_grid_xy'] = c_xy_im
        self.image_pipeline['centroids_grid_xz'] = c_xz_im
        self.image_pipeline['boundaries_grid_xy'] = b_xy_im
        self.image_pipeline['boundaries_grid_xz'] = b_xz_im

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
        self.image_pipeline['depth_blob_source'] = blob_image
        self.detected['depth_blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_image(self, centroids, boundaries):
        im = self.image_pipeline['image']
        detected = self._single_image_detection(image=im,
                                                blobs_area_filter=1500,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['image_blob_source'] = blob_image
        self.detected['image_blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_motion_depth(self, centroids, boundaries):
        diff = self.segmentation_model_depth.getSegmentedImage(whiteFG=False)
        detected = self._single_image_detection(image=diff,
                                                blobs_area_filter=1500,
                                                blobs_invert_image=False,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['motion_depth'] = diff
        self.image_pipeline['motion_depth_blob_source'] = blob_image
        self.detected['motion_depth_blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_with_motion_image(self, centroids, boundaries):
        diff = self.segmentation_model_image.getSegmentedImage(whiteFG=False)
        detected = self._single_image_detection(image=diff,
                                                blobs_area_filter=1500,
                                                blobs_invert_image=False,
                                                get_centroids=centroids,
                                                get_boundaries=boundaries)
        blob_image, blobs, centroids, boundaries = detected
        self.image_pipeline['motion_image'] = diff
        self.image_pipeline['motion_image_blob_source'] = blob_image
        self.detected['motion_image_blobs'] = blobs
        self.detected['centroids'] = centroids
        self.detected['boundaries'] = boundaries

    def _detect_combine_image_motion_image(self, centroids, boundaries):
        self._detect_with_image(centroids=False, boundaries=False)
        self._detect_with_motion_image(centroids=False, boundaries=False)
        blobs_im = self.detected['image_blobs']
        blobs_mo = self.detected['motion_image_blobs']
        return blobs_im, blobs_mo

    def _detect_combine_depth_motion_depth(self, centroids, boundaries):
        pass

    def _single_image_detection(self, image, blobs_area_filter=1500,
                                blobs_invert_image=True, get_centroids=True,
                                get_boundaries=False):
        blobs, blob_image = self._get_blobs(image, min_area=blobs_area_filter,
                                            invert_image=blobs_invert_image)
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

    def _get_blobs(self, image, min_area=0, invert_image=True):
        if invert_image:
            im = image.invert()
        else:
            im = image
        morphed = im.dilate(5)
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
        elif mode == 'combine_image_motion_image':
            self._detect_combine_image_motion_image(centroids=centroids,
                                                    boundaries=boundaries)
        elif mode == 'combine_depth_motion_depth':
            self._detect_combine_depth_motion_depth(centroids=centroids,
                                                    boundaries=boundaries)
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
        self._add_grids_to_image_pipeline()

    def get_results(self):
        results = dict()
        results.update(self.image_pipeline)
        results.update(self.detected)
        results.update({'centroids_grid' : self.centroids_grid,
                        'boundaries_grid' : self.boundaries_grid})
        return results

    def send_centroid_grid_coordinates(self, osc_client,
                                       message_name='/topview/centroids/xyz'):
        grid_points = self.centroids_grid.get_points()
        print('grid_points: %s' % grid_points)
        num_points = len(grid_points)
        if num_points > 0:
            pass
        self.centroids_grid.send_coordinates(osc_client)

    def send_boundaries_grid_coordinates(self, osc_client):
        self.boundaries_grid.send_coordinates(osc_client)


if __name__ == '__main__':
    d = Detector()
    m = ActorManager()
    disp = scv.Display()
    while disp.isNotDone():
        d.capture(image=True)
        d.detect(mode='image', centroids=True)
        results = d.get_results()
        m.update_points(results['centroids'])
        im = results['image']
        results['image_blobs'].image=im
        results['image_blobs'].draw()
        for c in results['centroids']:
            im.drawCircle(c, 6, color=scv.Color.RED, thickness=-1)
        for pt in m.points:
            im.drawCircle(pt.location[:-1], 5, color=pt.color, thickness=-1)
        im.save(disp)

