"""
RoiIo.py

Handles saving and loading of ROI sets from ZIP files, including metadata (state + tags).
Integrates with TinyRoiManager. Supports multiple loading strategies depending on file structure:
- With Lxxxx.roi naming and tags.json
- With Lxxxx.roi naming
- With no naming: infers labels from pixel-value at centroid position of an ROI in label image.

Author: Bart V.
Date: 2025-03-30
Version: 1.0
"""

import zipfile
import os
import json

from ij import IJ
from ij.io import RoiEncoder, RoiDecoder
from ij.gui import PolygonRoi, Roi
from ij.gui import TextRoi

from java.awt import Polygon
from java.awt import Color
from java.lang import Thread, Runnable

from StopWatch import StopWatch
from TinyRoiManager import TinyRoiManager

class RoiIo(object):
    _shared_instance=None

    def __new__(cls,gvars):
        if cls._shared_instance is None:
            cls._shared_instance = super(RoiIo, cls).__new__(cls)
        return cls._shared_instance

    def __init__(self,gvars):
        if hasattr(self, "_gvars"):
            IJ.log("RoiIo: singleton instance had already been created. This new call is ignored.")
            return
        self._gvars = gvars
        self._clean_up_list=[]
        self._rm = TinyRoiManager.getInstance2()
        self._imp_lbl=None
        self._temp_dir = os.getenv('TEMP') or './tmp'

    @staticmethod
    def getInstance():
        return RoiIo._shared_instance

    def _delete_later(self):
        def delete_job():
            try:
                for f in self._clean_up_list:
                    if os.path.exists(f):
                        os.remove(f)
            except Exception as e:
                print("Could not delete: " + f + " - " + str(e))
        thread = Thread(delete_job, "DeleteJobThread")
        thread.start()

    def save_to_zip(self,path, exclude_deleted=False):
        self._clean_up_list = []
        with self._rm.lock:
            tag_json = {}
            with zipfile.ZipFile(path, 'w') as zip_file:
                for i in range(1,self._rm.range_stop):
                    if self._rm.roi_array[i] and (not exclude_deleted or self._rm.states[i] != self._rm.ROI_STATE_DELETED):
                        tag_json["range_stop"] = self._rm.range_stop
                        name = self._rm.index_to_name[i]
                        roi = self._rm.roi_array[i]
                        roi_path = os.path.join(self._temp_dir , name + ".roi")
                        RoiEncoder.save(roi, roi_path)
                        zip_file.write(roi_path, arcname=name + ".roi")
                        self._clean_up_list.append(roi_path)
                        json_value = [self._rm.state_to_str(self._rm.states[i])] + list(self._rm.tags[i])
                        tag_json[name] = json_value
                json_data = json.dumps(tag_json)
                
                tags_path = os.path.join(self._temp_dir , "tags.json")
                with open(tags_path, 'w') as f:
                    f.write(json_data)
                zip_file.write(tags_path, arcname="tags.json")
                self._clean_up_list.append(tags_path)
        self._delete_later()

    def _is_valid_roi_name(self,name):
        return (
            name.endswith(".roi") and
            name.startswith("L") and
            name[1:-4].isdigit()
        )

    def _all_L_names(self,entry_list):
        return all(self._is_valid_roi_name(n) for n in entry_list)
        
    def _extract_rois(self,zip_file, roi_entries):
        for entry in roi_entries:
            zip_file.extract(entry, self._temp_dir)
        roi_paths = [os.path.join(self._temp_dir, entry) for entry in roi_entries]
        self._clean_up_list.extend(roi_paths)
        return roi_paths       

    def load_from_zip(self,path,imp_lbl):
        self._imp_lbl=imp_lbl

        with zipfile.ZipFile(path, 'r') as zip_file:
            entries = zip_file.namelist()
            roi_entries = [e for e in entries if e.endswith(".roi")]

            if "tags.json" in entries:
                self._load_zip_with_tags(zip_file, roi_entries)
            elif self._all_L_names(roi_entries):
                self._load_zip_with_L_names(zip_file, roi_entries)
            else:
                self._load_zip_without_tags(zip_file, roi_entries)

        self._delete_later()
        #self._rm.range_stop += 1

    def _load_zip_with_tags(self,zip_file, roi_entries):
        StopWatch().start("Reading ROIs: tags and state detected")
        print "Reading ROIs: tags and state detected"
        tags_path = os.path.join(self._temp_dir, "tags.json")

        with open(tags_path, 'wb') as f:
            f.write(zip_file.read("tags.json"))
        with open(tags_path, 'r') as f:
            tag_json = json.load(f)

        self._clean_up_list.append(tags_path)

        roi_paths = self._extract_rois(zip_file, roi_entries)
        if not (roi_paths and roi_entries):
            print "Reading ROIs: no data in ROI file"
            return
        self._rm.reset(num_of_rois=len(roi_paths))

        for entry, roi_path in zip(roi_entries, roi_paths):
            roi0 = RoiDecoder(roi_path).getRoi()
            roi_name = roi0.getName() or os.path.splitext(entry)[0]
            idx = int(roi_name[1:])
           
            p0 = roi0.getPolygon()
            p = Polygon(p0.xpoints, p0.ypoints, p0.npoints)
            roi = PolygonRoi(p, roi0.getType())
            roi.setName(roi_name)

            if roi_name in tag_json:
                state = self._rm.str_to_state(tag_json[roi_name][0])
                tags = set(tag_json[roi_name][1:])
            else:
                state = self._rm.ROI_STATE_ACTIVE
                tags = set()
            self._rm.add_1_tuple(name_idx_roi_state_tag=(roi_name,idx,roi,state,tags))
      

        StopWatch().stop("Reading ROIs") 

    def _load_zip_with_L_names(self,zip_file, roi_entries):
        StopWatch().start()
        print "Reading ROIs: all roi files have a name Lxxxx.roi, there were no tags or states detected"
        
        roi_paths = self._extract_rois(zip_file, roi_entries)
        if not (roi_entries and roi_paths):
            print "Reading ROIs: no data in ROI file"
            return
        num_of_rois=len(roi_entries)
        self._rm.reset(num_of_rois)

        max_digits=len(str(num_of_rois))
        dummy = TextRoi(0, 0, "L" + str(9).zfill(max_digits))
        b=dummy.getBounds()
        shift_y =  - b.height // 2
        dummy = None


        for entry, roi_path in zip(roi_entries, roi_paths):
            roi0 = RoiDecoder(roi_path).getRoi()
            roi_name = roi0.getName() or os.path.splitext(entry)[0]
            roi_idx = int(roi_name[1:])

            p0 = roi0.getPolygon()
            p = Polygon(p0.xpoints, p0.ypoints, p0.npoints)
            roi = PolygonRoi(p, roi0.getType())
            roi.setName(roi_name)

            state = self._rm.ROI_STATE_ACTIVE
            tags = set()

            self._rm.add_1_tuple(name_idx_roi_state_tag=(roi_name,roi_idx,roi,state,tags))
        
        
        StopWatch().stop("Reading ROIs")



    def _load_zip_without_tags(self,zip_file, roi_entries):

        def is_image_edge(roi, edge_h, edge_v):
            bounds = roi.getBounds()
            rx, ry, rw, rh = bounds.x, bounds.y, bounds.width, bounds.height
            return (rx <= 0 or ry <= 0 or (rx + rw) >= edge_h or (ry + rh) >= edge_v)
        
        StopWatch().start()
        print "Reading ROIs: ROI files have no names like Lxxxx.roi"
        
        ip = self._imp_lbl.getProcessor()
        pixels = ip.getPixels()
        width = self._imp_lbl.getWidth()
        height = self._imp_lbl.getHeight()
        edge_h = width - 1
        edge_v = height -1
        num_of_rois = len(roi_entries)
        self._rm.reset(num_of_rois)
        
        max_digits = len(str(num_of_rois))

        dummy = TextRoi(0, 0, "L" + str(9).zfill(max_digits))
        b = dummy.getBounds()
        shift_y = -b.height // 2

        load_zip_batch_size = self._gvars["load_zip_batch_size"]
        batches = [roi_entries[i:i + load_zip_batch_size] for i in range(0, num_of_rois, load_zip_batch_size)]

        threads = []
        
        remove_edges=self._gvars['remove_edges']
        remove_small=self._gvars['remove_small']
        size_threshold=self._gvars['size_threshold']
        
        for batch in batches:
            def make_task(entries=batch):
                class BatchTask(Runnable):
                    def run(inner_self):
                    
                        for entry in entries:
                            zip_file.extract(entry, self._temp_dir)
                        roi_paths = [os.path.join(self._temp_dir, entry) for entry in entries]
                        self._clean_up_list.extend(roi_paths)
                        #roi_paths = _extract_rois(zip_file, entries)

                        for entry, roi_path in zip(entries, roi_paths):
                            roi0 = RoiDecoder(roi_path).getRoi()
                            p0 = roi0.getPolygon()
                            p = Polygon(p0.xpoints, p0.ypoints, p0.npoints)
                            roi = PolygonRoi(p, roi0.getType())
                            stats = roi.getStatistics()
                            x = int(stats.xCentroid)
                            y = int(stats.yCentroid)
                            pixel_idx = y * width + x
                            idx = pixels[pixel_idx]
                            roi_name = "L" + str(idx).zfill(max_digits)
                            roi.setName(roi_name)

                            if remove_small and stats.area < size_threshold:
                                state= self._rm.ROI_STATE_DELETED
                                tags={"small"}
                            elif remove_edges and is_image_edge(roi,edge_h,edge_v):
                                state= self._rm.ROI_STATE_DELETED
                                tags={"edge.image"}
                            else:
                                state = self._rm.ROI_STATE_ACTIVE
                                tags = set()
                            self._rm.add_1_tuple(name_idx_roi_state_tag=(roi_name,idx,roi,state,tags))

                return BatchTask()

            t = Thread(make_task())
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        #self._rm.range_stop += 1
        StopWatch().stop("Reading ROIs")
