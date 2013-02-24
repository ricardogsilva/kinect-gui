import SimpleCV as scv
import freenect
import time
import numpy as np

class Kinect(scv.Kinect):

    def  __init__(self, device_number=0):
        scv.Kinect.__init__(self)
        self.device_number = device_number

    def getImage(self):
        """
        **SUMMARY**
        This method returns the Kinect camera image. 

        **RETURNS**
        The Kinect's color camera image. 

        **EXAMPLE**

        >>> k = Kinect()
        >>> while True:
        >>>   k.getImage().show()

        """
        video = freenect.sync_get_video(self.device_number)[0]
        self.capturetime = time.time()
        return scv.Image(video.transpose([1,0,2]), self)

    #low bits in this depth are stripped so it fits in an 8-bit image channel
    def getDepth(self):
        """
        **SUMMARY**
        This method returns the Kinect depth image. 

        **RETURNS**
        The Kinect's depth camera image as a grayscale image. 

        **EXAMPLE**

        >>> k = Kinect()
        >>> while True:
        >>>   d = k.getDepth()
        >>>   img = k.getImage()
        >>>   result = img.sideBySide(d)
        >>>   result.show()
        """

        depth = freenect.sync_get_depth(self.device_number)[0]
        self.capturetime = time.time()
        np.clip(depth, 0, 2**10 - 1, depth)
        depth >>= 2
        depth = depth.astype(np.uint8).transpose()
        return scv.Image(depth, self) 

    #we're going to also support a higher-resolution (11-bit) depth matrix
    #if you want to actually do computations with the depth
    def getDepthMatrix(self):
        self.capturetime = time.time()
        return freenect.sync_get_depth(self.device_number)[0]
