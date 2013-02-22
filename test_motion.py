#!/usr/bin/env python
#-*-coding: utf-8 -*-
import SimpleCV as scv
import numpy
import matplotlib.pyplot as plt

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

def get_centroids_map(original_image, centroids):
    grid_width = original_image.width
    grid_heigth = 254 # number of depth levels returned by the kinect
    grid = numpy.zeros((grid_heigth, grid_width), dtype=numpy.int8)
    for c in centroids:
        x, y, z = c
        grid[z, x] = y
    return grid

def get_diff(image, model):
    model.addImage(image)
    return model.getSegmentedImage(whiteFG=False)

def draw_blobs(image, blobs):
    blobs.image = image
    blobs.draw(color=scv.Color.RED, width=3)
    drawn_blobs = image.applyLayers()
    return drawn_blobs

def show_centroid_map(centroids, display):
    the_map = scv.Image(centroids_map_np)
    bigger = the_map.dilate(10)
    bigger.save(disp)

def show_detection(display, first_image, second_image):
    composite = first_image.sideBySide(second_image)
    composite.save(disp)

def morph(image, steps=5):
    #morphed = image.dilate(morph_steps).erode(morph_steps)
    morphed = image.erode(steps)
    return morphed


if __name__ == '__main__':
    k = scv.Kinect()
    first_depth = k.getDepth()
    seg = scv.RunningSegmentation()
    seg.addImage(first_depth)
    disp = scv.Display((first_depth.width*2, first_depth.height))
    while disp.isNotDone():
        dep = k.getDepth()
        diff_dep = get_diff(dep, seg)
        if diff_dep is not None:
            morphed = morph(diff_dep)
            blobs = morphed.findBlobs()
            if blobs is not None:
                #bigger_blobs = blobs.filter(blobs.area() > 1000)
                bigger_blobs = [blobs.sortArea()[-1]]
                centroids = []
                for b in bigger_blobs:
                    centroid = get_kinect_coords(dep, b)
                    if centroid is not None:
                        centroids.append(centroid)
                centroids_map_np = get_centroids_map(dep, centroids)
                the_map = scv.Image(centroids_map_np)
                #show_centroid_map(centroids, disp)
                drawn_blobs = draw_blobs(morphed, blobs)
                show_detection(disp, dep, drawn_blobs)
        else:
            disp.save(dep)
