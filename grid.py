#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import SimpleCV as scv

class GridWarper(object):

    # kinect calibration distances for the grid
    #YMIN = 1.23 # distance from the sensor to the nearest edge
    #YMAX = 4.52 # distance from the sensor to the farthest edge
    #XBMIN = -2.44 # distance from the farthest left corner to the middle
    #XBMAX = 2.44 # distance from the farthest right corner to the middle

    def __init__(self, width=640, height=480, ymin=1.23, ymax=4.52, 
                 xbmin=-2.44, xbmax=2.44):
        self.width = int(width)
        self.height = int(height)
        self.ymin = ymin
        self.ymax = ymax
        self.xbmin = xbmin
        self.xbmax = xbma=2.44
        self.norm_x, self.norm_y = self._compute_warp()

    def _compute_warp(self):
        # m_a: matrix degrees
        xb = np.linspace(self.xbmin, self.xbmax, self.width)
        yb = np.ones(self.width) * self.ymax
        a = np.arctan(xb / yb)
        m_a = np.zeros((self.height, self.width))
        for line in range(self.height):
            m_a[line, :] = a[:]
        # m_y: matrix y
        y = np.linspace(self.ymin, self.ymax, self.height)
        m_y = np.zeros((self.height, self.width))
        for col in range(self.width):
            m_y[:, col]  = y[:]
        m_x = m_y * np.tan(m_a)
        #normalized map coordinates
        norm_x = (m_x[:] - self.xbmin) / (self.xbmax - self.xbmin)
        norm_y = (m_y[:] - self.ymin) / (self.ymax - self.ymin)
        return norm_x, norm_y

    def get_coords(self, raw_y, raw_x):
        warped_x = self.norm_x[raw_y, raw_x]
        warped_y = self.norm_y[raw_y, raw_x]
        return warped_y, warped_x


class Grid(object):

    def __init__(self, lines=480, cols=640, depth=100,
                 real_min_width=0, real_max_width=640,
                 real_min_height=0, real_max_height=480,
                 real_min_depth=200, real_max_depth=254):
        '''
        Inputs:

            lines - Height of the grid.
            cols - Width of the grid.
            depth - Depth of the grid.
            real_min_width - The minimum width value returned by the sensor.
            real_max_width - The maximum width value returned by the sensor.
            real_min_height - The minimum height value returned by the sensor.
            real_max_height - The maximum height value returned by the sensor.
            real_min_depth - The minimum depth value returned by the sensor.
            real_max_depth - The maximum depth value returned by the sensor.

        '''

        self.DEPTH_VALUE_POINT = 0
        self.WIDTH = float(cols)
        self.HEIGHT = float(lines)
        self.DEPTH = float(depth)
        self.REAL_MIN_WIDTH = real_min_width
        self.REAL_MAX_WIDTH = real_max_width
        self.REAL_MIN_HEIGHT = real_min_height
        self.REAL_MAX_HEIGHT = real_max_height
        self.REAL_MIN_DEPTH = real_min_depth
        self.REAL_MAX_DEPTH = real_max_depth
        self.real_width_range = real_max_width - real_min_width
        self.real_height_range = real_max_height - real_min_height
        self.real_depth_range = real_max_depth - real_min_depth
        self.xy_grid = np.ones((self.HEIGHT, self.WIDTH), dtype=np.int8) * 255
        self.xz_grid = np.ones((self.DEPTH, self.WIDTH), dtype=np.int8) * 255
        self.xz_warper = GridWarper(width=self.WIDTH, height=self.DEPTH)

    def _rescale_point(self, point):
        '''
        Return a new point (a 3 element list) with rescaled depth,
        according to the grid's depth.
        '''

        x, y, z = point
        r_x = ((x - self.REAL_MIN_WIDTH) * self.WIDTH /
                self.real_width_range)
        r_y = ((y - self.REAL_MIN_HEIGHT) * self.HEIGHT /
                self.real_height_range)
        r_z = ((z - self.REAL_MIN_DEPTH) * self.DEPTH /
                self.real_depth_range)
        if r_x <= 0 or r_x >= self.WIDTH:
            r_x = None
        if r_y <= 0 or r_y >= self.HEIGHT:
            r_y = None
        if r_z <= 0 or r_z >= self.DEPTH:
            r_z = None
        if z == 0: # to cater for 2d images (normal camera, without depth)
            r_z = self.DEPTH - 1
        if r_x is None or r_y is None or r_z is None:
            result = None
        else:
            result = [r_x, r_y, r_z]
        return result

    def update_grid(self, points):
        '''
        Update the detected points' coordinates on the grid.

        Inputs

            points - a list of points with the raw x, y, z coordinates
                read from the Kinect sensor

        Returns: Nothing
        '''

        self.xy_grid.fill(255)
        self.xz_grid.fill(255)
        for p in points:
            #print('old coordinates: %s,' % (p,))
            the_point = self._rescale_point(p)
            if the_point is not None:
                x, y, z = the_point
                #print('rescaled coordinates: %s, %s, %s' % (x, y, z))
                warped_z, warped_x = self.xz_warper.get_coords(z, x)
                #print('warped coordinates: %s, %s' % (warped_x, warped_z))
                grid_x = np.round(warped_x * (self.WIDTH - 1))
                grid_z = np.round(warped_z * (self.DEPTH - 1))
                self.xz_grid[grid_z, grid_x] = self.DEPTH_VALUE_POINT
                self.xy_grid[y, grid_x] = self.DEPTH_VALUE_POINT

    def get_image(self, grid_type='xz'):
        if grid_type == 'xy':
            grid = self.xy_grid
        elif grid_type == 'xz':
            grid = self.xz_grid
        grid_im = scv.Image(grid.transpose())
        morphed = grid_im.erode(10)
        return morphed

    def get_points(self):
        '''
        Return the coordinates on the grids of points.
        '''
        coords_xz = np.argwhere(self.xz_grid == self.DEPTH_VALUE_POINT)
        coords_xy = np.argwhere(self.xy_grid == self.DEPTH_VALUE_POINT)
        points = []
        for pt in range(coords_xz.shape[0]):
            x = coords_xz[pt, 1] / self.WIDTH
            y = coords_xy[pt, 0] / self.HEIGHT
            z = coords_xz[pt, 0] / self.DEPTH
            points.append((x, y, z))

    #def send_coordinates(self, osc_client, message_name):
    #    coords_xz = np.argwhere(self.xz_grid == self.DEPTH_VALUE_POINT)
    #    coords_xy = np.argwhere(self.xy_grid == self.DEPTH_VALUE_POINT)
    #    print('coords_xz: %s' % coords_xz)
    #    print('coords_xy: %s' % coords_xy)
    #    num_points = coords_xz.shape[0]
    #    if num_points > 0:
    #        #coords = np.zeros((num_points, 3))
    #        coords = []
    #        coords.append(num_points)
    #        for pt in range(num_points):
    #            #coords[pt, 0] = coords_xz[pt, 1] / self.WIDTH
    #            #coords[pt, 1] = coords_xy[pt, 0] / self.HEIGHT
    #            #coords[pt, 2] = coords_xz[pt, 0] / self.DEPTH
    #            coords.append(coords_xz[pt, 1] / self.WIDTH)
    #            coords.append(coords_xy[pt, 0] / self.HEIGHT)
    #            coords.append(coords_xz[pt, 0] / self.DEPTH)
    #        print('coords: %s' % coords)
    #        #osc_client.send_message(message_name, coords)
    #        print('----------')
