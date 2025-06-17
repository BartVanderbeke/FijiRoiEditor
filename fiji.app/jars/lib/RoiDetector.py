"""
roi_detector.py

Background worker that scans a labeled image for unprocessed regions and generates ROIs using ImageJ's Wand tool.
unprocessed = not assigned to an ROI yet
Intended to be run in parallel by multiple threads to speed up ROI detection.

Author: Bart V. + Elisa
Date: 2025-03-30
Version: 1.0
"""

from ij import IJ
from ij.gui import Wand, PolygonRoi, Roi
from java.awt import Polygon
from java.lang import Runnable
from jarray import array

class RoiDetector(Runnable):
    def __init__(self, ip, pixels, roi_array, start_idx, end_idx, step, width):
        """
        Initialize a parallel ROI detector.

        Parameters:
        - imp: ImagePlus (label image)
        - roi_array: shared array to store detected ROIs, indexed by label value
        - start_idx: start pixel index (int)
        - end_idx: end pixel index (exclusive)
        - step: step size (usually number of threads)
        - width: image width (used for x/y coordinate calculation)
        """
        #self.imp = imp
        self.roi_array = roi_array
        self.start_idx = start_idx
        self.stop_idx = end_idx
        self.step_idx = step
        self.width = width
        self.counter = 0
        #self.short_to_float = array([float(x) for x in range(len(roi_array))], 'f')
        self.wand = Wand(ip)
        self.pixels=pixels

    def run(self):
        """
        Scan the assigned pixels for unprocessed labels and generate ROIs
        by tracing the boundary using ImageJ's Wand tool.
        """
        wand=self.wand
        pixels=self.pixels
        current_pixel_value,x,y,target_value=0,0,0,0.0
        #for pxl_idx in range(self.start_idx, self.stop_idx, self.step_idx):
        pxl_idx = self.start_idx
        while pxl_idx < self.stop_idx:        
            current_pixel_value = pixels[pxl_idx]

            if not self.roi_array[current_pixel_value]:
                self.counter+=1

                y = pxl_idx // self.width
                x = pxl_idx % self.width
                target_value = float(current_pixel_value)
                #target_value = self.short_to_float[current_pixel_value]

                wand.autoOutline(x, y, target_value, target_value, Wand.EIGHT_CONNECTED)

                #if wand.npoints > 0:
                poly = Polygon(wand.xpoints, wand.ypoints, wand.npoints)
                roi = PolygonRoi(poly, Roi.TRACED_ROI)
                self.roi_array[current_pixel_value] = roi
            pxl_idx += self.step_idx