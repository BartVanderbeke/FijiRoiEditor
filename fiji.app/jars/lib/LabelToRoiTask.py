from javax.swing import SwingWorker
from java.lang import Thread,Runtime
from ij import IJ

import datetime
import math

from ij.gui import Roi
from TinyRoiManager import TinyRoiManager as RoiManager
from RoiIo import RoiIo
from RoiDetector import RoiDetector
from ij.gui import TextRoi

from jarray import zeros
from java.lang import String
from java.awt import Color

from StopWatch import StopWatch

def is_image_edge(roi, edge_h, edge_v):
    bounds = roi.getBounds()
    rx, ry, rw, rh = bounds.x, bounds.y, bounds.width, bounds.height

    return (rx <= 0 or ry <= 0 or (rx + rw) >= edge_h or (ry + rh) >= edge_v)

class LabelToRoiTask(SwingWorker):
    def __init__(self, imp_lbl, gvars,continuation_after_loading):
        SwingWorker.__init__(self)
        self.imp_lbl = imp_lbl.duplicate()
        #self.roi_array = None
        self.width= None
        self.height = None
        self.good_to_start=False
        self.roi_names = None
        self.gvars=gvars
        self.continuation_after_loading=continuation_after_loading
        self.max_label_found = -1

    def start(self):
        self.width=self.imp_lbl.getWidth()
        self.height = self.imp_lbl.getHeight()
        IJ.log("Computing ROIs started")
        self.good_to_start=True
        self.execute()

    def doInBackground(self):
        rm = RoiManager.getInstance2()
        rm.reset(-1)
        ri= RoiIo.getInstance()
        gvars=self.gvars
        if not self.good_to_start:
            IJ.log("LabelToRoiTask: Use start to start")
            return
        self.good_to_start=False
        
        width=self.width
        height=self.height
        num_logical_processors = Runtime.getRuntime().availableProcessors()
        StopWatch().start()


        edge_h = width - 1
        edge_v = height -1
        
        remove_edges=gvars['remove_edges']
        remove_small=gvars['remove_small']
        size_threshold=gvars['size_threshold']
        
        ip = self.imp_lbl.getProcessor()
        pixels = ip.getPixels()

        
        step=7 # not all pixels are checked, every 'steps' are checked
        
        n_pixels = width * height
        pixels_per_proc = gvars["pixels_per_logical_processor"]
        num_threads = min(n_pixels // pixels_per_proc   + 1, num_logical_processors)
        chunk_size = int((n_pixels + num_threads - 1) / num_threads)

        start_idx = [t * chunk_size for t in range(num_threads)]
        stop_idx = [min((t + 1) * chunk_size, n_pixels) for t in range(num_threads)]
        runnables = [
            RoiDetector(ip,pixels, rm.roi_array, start_idx[t], stop_idx[t], step, width)
            for t in range(num_threads)
        ]
        threads = [Thread(r) for r in runnables]

        for thread in threads:
            thread.setPriority(Thread.MAX_PRIORITY)
            thread.start()
        IJ.log("#processors: "+str(num_logical_processors)+" | #threads started: "+ str(num_threads))
        
        for thread in threads:
            thread.join()
            
        self.max_label_found = sum(r.counter for r in runnables)
        rm.set_range_stop(num_of_rois=self.max_label_found)

        StopWatch().stop("Computing ROIs")
        StopWatch().start()
        
        
        # Calculate the number of digits for the name of the ROI (padding with zeros)
        max_digits = len(str(self.max_label_found))
        
        self.deleted_too_small_counter=0
        self.deleted_at_edge_counter =0
        self.added_roi_counter =0
        for roi_idx in range(1,rm.range_stop):
            this_roi= rm.roi_array[roi_idx]
            # 'None' rois should not be encountered
            # if not this_roi:
                # break
            roi_name = "L" + str(roi_idx).zfill(max_digits)
            this_roi.setName(roi_name)
            stats = this_roi.getStatistics()
            if remove_small and stats.area < size_threshold:
                state= rm.ROI_STATE_DELETED
                tags={"small"}
                self.deleted_too_small_counter+=1
            elif remove_edges and is_image_edge(this_roi,edge_h,edge_v):
                state= rm.ROI_STATE_DELETED
                tags={"edge.image"}
                self.deleted_at_edge_counter +=1
            else:
                state = rm.ROI_STATE_ACTIVE
                tags = set()
                self.added_roi_counter+=1
            rm.add_1_tuple(name_idx_roi_state_tag=(roi_name,roi_idx,this_roi,state,tags))

        StopWatch().stop("Adding ROIs")
        
        ## We save a temporary RoiSet
        #rm=RoiManager.getInstance2()
        temp_roi_path = self.gvars['tempFile']
        ri.save_to_zip(temp_roi_path)

    def done(self):
        self.get()  #raise exception if abnormal completion

        print "Ignored too small ROIs: ",str(self.deleted_too_small_counter)
        print "Ignored ROIS at edge  : ",str(self.deleted_at_edge_counter)
        print "Added ROIs            : ",str(self.added_roi_counter)
        

        
        self.continuation_after_loading()
