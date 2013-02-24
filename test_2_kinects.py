#!/usr/bin/env python

import SimpleCV as scv
from multiplekinects import Kinect

if __name__ == '__main__':
    k0 = Kinect(0)
    k1 = Kinect(1)
    first = k0.getImage()
    disp = scv.Display((900, 700))
    while disp.isNotDone():
        d0, im0 = k0.getDepth().invert(), k0.getImage()
        d1, im1 = k1.getDepth().invert(), k1.getImage()
        comp_im = im0.sideBySide(im1)
        comp_dep = d0.sideBySide(d1)
        composite = comp_im.sideBySide(comp_dep, side='bottom')
        composite.save(disp)
