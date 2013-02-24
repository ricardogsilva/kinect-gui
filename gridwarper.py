#!/usr/bin/env python
# -*- coding : utf-8 -*- 
import numpy as np
#
## grid dimension
#w=640
#h=254
#
##constants for kinect calibration
#ymin=1.23
#ymax=4.52
#xbmin=-2.44
#xbmax=2.44
#
## m_a: matrix degrees
#xb=np.linspace(xbmin,xbmax,w)
#yb=np.ones((w))*ymax
#a=np.arctan(xb/yb)
#m_a=np.zeros((h,w))
#for l in range(h):
#    m_a[l,:]=a[:]
#
## m_y: matrix y
#y=linspace(ymin,ymax+ystep,ystep)
#m_y=np.zeros((h,w))
#for c in range(w):
#    m_y[:,c]=y[:]
#
##normalized map coordinates 
#norm_X=(m_x[:]-xbmin)/(xbmax-xbmin)
#norm_Y=(m_y[:]-ymin)/(ymax-ymin)
#
class GridWarper(object):

    # kinect calibration distances for the grid
    YMIN = 1.23 # distance from the sensor to the nearest edge
    YMAX = 4.52 # distance from the sensor to the farthest edge
    XBMIN = -2.44 # distance from the farthest left corner to the middle
    XBMAX = 2.44 # distance from the farthest right corner to the middle

    def __init__(self, width=640, height=480):
        self.width = int(width)
        self.height = int(height)
        self.norm_x, self.norm_y = self._compute_warp()

    def _compute_warp(self):
        # m_a: matrix degrees
        xb = np.linspace(self.XBMIN, self.XBMAX, self.width)
        yb = np.ones(self.width) * self.YMAX
        a = np.arctan(xb / yb)
        m_a = np.zeros((self.height, self.width))
        for line in range(self.height):
            m_a[line, :] = a[:]
        # m_y: matrix y
        y = np.linspace(self.YMIN, self.YMAX, self.height)
        m_y = np.zeros((self.height, self.width))
        for col in range(self.width):
            m_y[:, col]  = y[:]
        m_x = m_y * np.tan(m_a)
        #normalized map coordinates
        norm_x = (m_x[:] - self.XBMIN) / (self.XBMAX - self.XBMIN)
        norm_y = (m_y[:] - self.YMIN) / (self.YMAX - self.YMIN)
        return norm_x, norm_y

    def get_coords(self, raw_y, raw_x):
        warped_x = self.norm_x[raw_y, raw_x]
        warped_y = self.norm_y[raw_y, raw_x]
        return warped_y, warped_x
