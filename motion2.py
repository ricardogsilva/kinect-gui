#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
'''

import SimpleCV as scv
import numpy
import scipy.ndimage as ndimage
import OSC

def get_depth_blobs(depth_im):
    morphed = depth_im.dilate(5)
    blobs = morphed.findBlobs()
    return blobs

def get_motion_blobs(motion_im):
    blobs = motion_im.findBlobs()
    return blobs

def count_pixels(im):
    hist, bins = numpy.histogram(im, bins=range(256))
    b = list(bins)
    b.pop(0)
    counts = zip(b, hist)
    counts.sort(key=lambda item:item[1], reverse=True)
    return counts

def simplify_image(image, intensity_levels=20):
    filtered = image.smooth(aperture=(21, 21))
    #im = image.getNumpy()[:,:,0]
    im = filtered.getNumpy()[:,:,0]
    #filtered = ndimage.gaussian_filter(im, 0.1)
    counts = count_pixels(im)
    top = [c[0] for c in counts[:20]]
    try:
        top.remove(255)
    except ValueError:
        pass
    top.sort()
    simpler = numpy.zeros(im.shape)
    for i in top:
        simpler += (im == i) * i
    return simpler

def get_kinect_coords(original_image, blob):
    point = None
    x, y = blob.centroid()
    old_image = blob.image
    blob.image = original_image
    cropped = blob.crop()
    np_im = cropped.getNumpy()
    im_values = set(np_im.flat)
    im_values.discard(255) # not a real sensor measurement
    intensity_values = list(im_values)
    if len(intensity_values) > 0:
        average_intensity = int(numpy.average(intensity_values))
        point = [int(x), int(y), average_intensity]
    blob.image = old_image
    return point


class OSCCommunicator(object):

    def __init__(self, server_ip, client_ip, server_port=5000, client_port=8000):
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
        self.server.addMsgHandler('/1/toggle1', self._print_msg)
        self.client = OSC.OSCClient()
        self.client.connect((client_ip, client_port))

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

    def _normalize_point(self, point):
        '''
        Return a new point (a 3 element list) with normalized depth,
        according to the grid's depth.
        '''

        x, y, z = point
        norm_x = (((x - self.REAL_MIN_WIDTH) * self.WIDTH /
                self.real_width_range) + 0) / self.WIDTH
        norm_y = (((y - self.REAL_MIN_HEIGHT) * self.HEIGHT /
                self.real_height_range) + 0) / self.HEIGHT
        norm_z = ((z - self.REAL_MIN_DEPTH) * self.DEPTH /
                self.real_depth_range) + 0
        if norm_x < 0:
            norm_x = 0
        elif norm_x >= self.WIDTH:
            #norm_x = self.WIDTH - 1
            norm_x = 1
        if norm_y < 0:
            norm_y = 0
        elif norm_y >= self.HEIGHT:
            #norm_y = self.HEIGHT - 1
            norm_y = 1
        norm_z = (self.DEPTH - norm_z) / self.DEPTH
        if norm_z < 0:
            norm_z = 0
        elif norm_z >= self.DEPTH:
            #norm_z = self.DEPTH - 1
            norm_z = 1
        return [norm_x, norm_y, norm_z]

    def update_grid(self, *points):
        self.xy_grid.fill(255)
        self.xz_grid.fill(255)
        for p in points:
            print('old coordinates: %s' % p)
            x, y, z = self._normalize_point(p)
            print('normalized coordinates: %s, %s, %s' % (x, y, z))
            self.xy_grid[y, x] = z
            self.xz_grid[z, x] = 0

    def get_image(self, grid_type='xz'):
        if grid_type == 'xy':
            grid = self.xy_grid
        elif grid_type == 'xz':
            grid = self.xz_grid
        grid_im = scv.Image(grid.transpose())
        #morphed = grid_im.dilate(5)
        morphed = grid_im.erode(5)
        return morphed


if __name__ == '__main__':
    osc_comm = OSCCommunicator(server_ip='192.168.1.201', client_ip='127.0.1.1')
    MIN_AREA_DEPTH = 1500
    k = scv.Kinect()
    first = k.getDepth()
    g = Grid(cols=first.width, lines=first.height, depth=480, real_min_depth=200)
    previous = first
    disp = scv.Display((first.width*2, first.height))
    while disp.isNotDone():
        osc_request = osc_comm.server.handle_request()
        while osc_request is not None:
            osc_request = osc_comm.server.handle_request()
        d = k.getDepth().invert()
        d_blobs = get_depth_blobs(d)
        if d_blobs is not None:
            big_blobs = d_blobs.filter(d_blobs.area() > MIN_AREA_DEPTH)
            if len(big_blobs) > 0:
                depth_centroids = []
                for b in big_blobs:
                    depth_centroids.append(get_kinect_coords(d.invert(), b))
                normalized_centroids = map(lambda i: i[2]*100/254, 
                                           depth_centroids)
                g.update_grid(*depth_centroids)
                big_blobs.image = d
                big_blobs.draw(color=scv.Color.RED, width=3)
        #diff = (d - previous).binarize(0).invert()
        #motion_blobs = get_motion_blobs(diff)
        #if motion_blobs is not None:
        #    bigger_blobs = motion_blobs.filter(motion_blobs.area() > 1000)
        #    if len(bigger_blobs) > 1:
        #        motion_centroids = []
        #        bigger_blobs.image = diff
        #        for b in bigger_blobs[-2:]:
        #            b.draw(color=scv.Color.RED, width=-1, alpha=170)
        #            motion_centroids.append(get_kinect_coords(d.invert(), b))
        #        g.update_grid(*motion_centroids)
        drawn_d = d.applyLayers()
        #drawn_diff = diff.applyLayers()
        grid_im = g.get_image('xz')
        #composite = drawn_diff.sideBySide(grid_im, scale=False)
        composite = drawn_d.sideBySide(grid_im, scale=False)
        composite.save(disp)
        previous = d
