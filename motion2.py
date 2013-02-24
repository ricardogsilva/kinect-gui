#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
'''

import SimpleCV as scv
import numpy
import scipy.ndimage as ndimage
import OSC
from gridwarper import GridWarper

def get_blobs(depth_im):
    morphed = depth_im.dilate(5)
    #bin_ = morphed.binarize(1).invert()
    bin_ = morphed
    blobs = bin_.findBlobs()
    return blobs

def count_pixels(im):
    hist, bins = numpy.histogram(im, bins=range(256))
    b = list(bins)
    b.pop(0)
    counts = zip(b, hist)
    counts.sort(key=lambda item:item[1], reverse=True)
    return counts

def get_kinect_coords(original_image, blob):
    point = None
    x, y = blob.centroid()
    old_image = blob.image
    blob.image = original_image
    cropped = blob.crop()
    np_im = cropped.getNumpy()
    counts = count_pixels(np_im)
    useful_counts = numpy.asarray([c for c in counts if c[0]!=255 and c[1]>0])
    if len(useful_counts) > 0:
        average_intensity = numpy.average(useful_counts[:, 0],
                                          weights=useful_counts[:, 1])
        point = [int(x), int(y), average_intensity]
    blob.image = old_image
    return point


class OSCCommunicator(object):

    def __init__(self, server_ip, client_ip, 
                 server_port=5000, client_port=8000,
                 send_OSC=True):
        '''
        Inputs:

            server_ip - A string holding this machine's ip address.

            client_ip - A string holding the ip address of the machine where
                we will send OSC messages.

            server_port - An integer specifying the port number that we will
                use on this machine for the server.

            client_port - An integer specifying the port number of the
                machine that will receive our sent OSC messages.
        '''

        self.server = OSC.OSCServer((server_ip, server_port))
        self.server.timeout = 0
        #self.server.addMsgHandler('/1/toggle1', self._print_msg)
        self.server.addMsgHandler('/1/toggle1', self._toggle_send_OSC)
        self.client = OSC.OSCClient()
        self.client.connect((client_ip, client_port))
        self.send_OSC = send_OSC

    def send_message(self, address, *values):
        message = OSC.OSCMessage(address)
        for v in values:
            message.append(v)
        self.client.send(message)

    def _print_msg(self, address, tags, data, client_address):
        print('address: %s' % address)
        print('tags: %s' % tags)
        print('data: %s' % data)
        print('client_address: %s' % (client_address,))

    def _toggle_send_OSC(self, address, tags, data, client_address):
        self.send_OSC = bool(data[0])


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
        self.xy_grid = numpy.ones((self.HEIGHT, self.WIDTH), dtype=numpy.int8) * 255
        self.xz_grid = numpy.ones((self.DEPTH, self.WIDTH), dtype=numpy.int8) * 255
        self.warper = GridWarper(width=self.WIDTH, height=self.DEPTH)

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
        if r_y <= 0 or r_x >= self.HEIGHT:
            r_y = None
        if r_z <= 0 or r_z >= self.DEPTH:
            r_z = None
        if r_x is None or r_y is None or r_z is None:
            result = None
        else:
            result = [r_x, r_y, r_z]
        return result

    def update_grid(self, *points):
        self.xy_grid.fill(255)
        self.xz_grid.fill(255)
        for p in points:
            #print('old coordinates: %s' % p)
            the_point = self._rescale_point(p)
            if the_point is not None:
                x, y, z = the_point
                #print('rescaled coordinates: %s, %s, %s' % (x, y, z))
                warped_z, warped_x = self.warper.get_coords(z, x)
                #print('warped coordinates: %s, %s' % (warped_x, warped_z))
                grid_x = numpy.round(warped_x * (self.WIDTH - 1))
                grid_z = numpy.round(warped_z * (self.DEPTH - 1))
                self.xz_grid[grid_z, grid_x] = self.DEPTH_VALUE_POINT
                self.xy_grid[y, grid_x] = self.DEPTH_VALUE_POINT

    def get_image(self, grid_type='xz'):
        if grid_type == 'xy':
            grid = self.xy_grid
        elif grid_type == 'xz':
            grid = self.xz_grid
        grid_im = scv.Image(grid.transpose())
        morphed = grid_im.erode(5)
        return morphed

    def send_coordinates(self, osc_client):
        coords_xz = numpy.argwhere(self.xz_grid == self.DEPTH_VALUE_POINT)
        coords_xy = numpy.argwhere(self.xy_grid == self.DEPTH_VALUE_POINT)
        print('coords_xz: %s' % coords_xz)
        print('coords_xy: %s' % coords_xy)
        num_points = coords_xz.shape[0]
        if num_points > 0:
            #coords = numpy.zeros((num_points, 3))
            coords = []
            coords.append(num_points)
            for pt in range(num_points):
                #coords[pt, 0] = coords_xz[pt, 1] / self.WIDTH
                #coords[pt, 1] = coords_xy[pt, 0] / self.HEIGHT
                #coords[pt, 2] = coords_xz[pt, 0] / self.DEPTH
                coords.append(coords_xz[pt, 1] / self.WIDTH)
                coords.append(coords_xy[pt, 0] / self.HEIGHT)
                coords.append(coords_xz[pt, 0] / self.DEPTH)
            print('coords: %s' % coords)
            #osc_client.send_message('/topview/xyz', coords)
            print('----------')


if __name__ == '__main__':
    osc_comm = OSCCommunicator(server_ip='192.168.1.201',
                               client_ip='192.168.1.201', 
                               client_port=9000, send_OSC=False)
    MIN_AREA_DEPTH = 1500
    k = scv.Kinect()
    first = k.getDepth()
    disp = scv.Display((first.width*2, first.height))
    g = Grid(cols=first.width, lines=first.height, 
             depth=480, real_min_depth=200)
    while disp.isNotDone():
        osc_request = osc_comm.server.handle_request()
        if osc_comm.send_OSC:
            print('send OSC')
        while osc_request is not None:
            osc_request = osc_comm.server.handle_request()
        d = k.getDepth()
        d_for_draw = d.invert()
        blobs = get_blobs(d.invert())
        centroids = []
        if blobs is not None:
            big_blobs = blobs.filter(blobs.area() > MIN_AREA_DEPTH)
            if len(big_blobs) > 0:
                for b in big_blobs:
                    centroid = get_kinect_coords(d, b)
                    if centroid is not None:
                        centroids.append(centroid)
                if osc_comm.send_OSC:
                    g.send_coordinates(osc_comm)
                big_blobs.image = d_for_draw
                big_blobs.draw(color=scv.Color.RED, width=3)
        g.update_grid(*centroids)
        drawn_d = d_for_draw.applyLayers()
        grid_im = g.get_image('xz')
        composite = drawn_d.sideBySide(grid_im, scale=False)
        composite.save(disp)
