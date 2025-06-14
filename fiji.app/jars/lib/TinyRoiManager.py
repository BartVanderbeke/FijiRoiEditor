"""
TinyRoiManager.py

A minimalistic, thread-safe ROI manager for ImageJ/Fiji that stores ROI objects, their states,
tags, and provides fast access and manipulation. This class is designed to be efficient for
batch-processing large amounts of ROIs in headless or semi-automated workflows.

It uses parallel arrays for ROI data, allowing quick state toggling, filtering, and metadata storage.
Supports singleton pattern for global access within a session.

Author: Bart V.
Date: 2025-03-30
Version: 1.0
"""

import zipfile
import os
import json
import threading
import math

from ij import IJ
from ij.io import RoiEncoder, RoiDecoder
from ij.gui import PolygonRoi, Roi
from ij.gui import TextRoi
from java.awt import Polygon
from java.awt import Rectangle
from java.awt import Color

from java.lang import String
from java.lang import Thread, Runnable

from jarray import zeros

from StopWatch import StopWatch

class TinyRoiManager(object):
    # ROI state constants
    ROI_STATE_ACTIVE = 0
    ROI_STATE_DELETED = -1
    ROI_STATE_SELECTED = +1

    # Singleton instance reference
    _singleton_instance = None

    def __new__(cls, gvars):
        if cls._singleton_instance is None:
            cls._singleton_instance = super(TinyRoiManager, cls).__new__(cls)
            cls._singleton_instance.gvars = gvars
        return cls._singleton_instance

    def __init__(self, gvars):
        if hasattr(self, "reserved_size"):
            IJ.log("TinyRoiManager: singleton instance had already been created & initialized. This new call is ignored.")
            return

        self.reserved_size = gvars["max_number_of_rois"]

        self.roi_array = zeros(self.reserved_size, Roi)
        self.label_array = zeros(self.reserved_size, TextRoi)
        self.states = zeros(self.reserved_size, 'b')
        self.reason_of_selection = zeros(self.reserved_size, String)
        self.tags = [set() for _ in range(self.reserved_size)]

        self.name_to_index = {}
        self.index_to_name = zeros(self.reserved_size, String)
        self.lock = threading.Lock()
        self.range_stop = -1  # highest label number + 1

        # Initialize index 0 with placeholder empty ROI
        empty_poly = Polygon()
        empty_roi = PolygonRoi(empty_poly, Roi.TRACED_ROI)
        empty_roi.setName("EMPTY")
        self.roi_array[0] = empty_roi
        
        self.label_array[0] = TextRoi(0, 0, "NOT ME")
        self.label_shift_y = None
        self.name_length = None
        

    def reset(self,num_of_rois):
        """Clears all ROIs from index 1 onward, preserving index 0."""
        """0 is a dummy"""
        with self.lock:
            cleanup_range = max(self.range_stop,num_of_rois+1)
            for idx in range(1,cleanup_range):
                self.roi_array[idx] = None
                self.states[idx] = 0
                self.tags[idx] = set()
                self.reason_of_selection[idx] = ""
        self.set_range_stop(num_of_rois)    

    def set_range_stop(self,num_of_rois):
        self.range_stop = num_of_rois + 1
        max_digits = len(str(num_of_rois))
        self.name_length=max_digits+1
        text_roi_dummy = TextRoi(0, 0, "L" + str(9).zfill(max_digits))
        b = text_roi_dummy.getBounds()
        self.label_shift_y = b.height // 4

    @staticmethod
    def getInstance2():
        return TinyRoiManager._singleton_instance

    @staticmethod
    def getInstance():
        return TinyRoiManager._singleton_instance

    @staticmethod
    def state_to_str(state):
        if state == TinyRoiManager.ROI_STATE_DELETED:
            return "ROI_STATE_DELETED"
        elif state == TinyRoiManager.ROI_STATE_SELECTED:
            return "ROI_STATE_SELECTED"
        else:
            return "ROI_STATE_ACTIVE"

    @staticmethod
    def str_to_state(state):
        if state == "ROI_STATE_DELETED":
            return TinyRoiManager.ROI_STATE_DELETED
        elif state == "ROI_STATE_SELECTED":
            return TinyRoiManager.ROI_STATE_SELECTED
        else:
            return TinyRoiManager.ROI_STATE_ACTIVE

    def _resolve_names(self, rois_or_names):
        """Helper method to convert ROI objects or names to a list of names."""
        if not isinstance(rois_or_names, (list, tuple, set)):
            rois_or_names = [rois_or_names]
        return [r.getName() if hasattr(r, 'getName') else r for r in rois_or_names]

    def select_within(self, rectangle, additive=False):
        """Select all ROIs whose bounding rectangles are fully within the given rectangle."""
        with self.lock:
            if not additive:
                self.unselect_all()

            rect_xmin = rectangle.x
            rect_ymin = rectangle.y
            rect_xmax = rectangle.x + rectangle.width
            rect_ymax = rectangle.y + rectangle.height

            for idx in range(1, self.range_stop):
                if self.states[idx] != self.ROI_STATE_ACTIVE:
                    continue
                roi = self.roi_array[idx]
                bounds = roi.getBounds()
                if (rect_xmin <= bounds.x and
                    rect_ymin <= bounds.y and
                    rect_xmax >= bounds.x + bounds.width and
                    rect_ymax >= bounds.y + bounds.height):
                    self.states[idx] = self.ROI_STATE_SELECTED
                    self.reason_of_selection[idx] = "manual"

    def unselect_all(self):
        """Sets all selected ROIs back to active."""
        with self.lock:
            for idx in range(1, self.range_stop):
                if self.states[idx] == self.ROI_STATE_SELECTED:
                    self.states[idx] = self.ROI_STATE_ACTIVE
                    self.reason_of_selection[idx] = ""

    def select(self, rois_or_names, reason_of_selection=None, additive=False):
        """Selects the specified ROIs, optionally preserving previous selections."""
        with self.lock:
            names = self._resolve_names(rois_or_names)
            if not additive:
                self.unselect_all()
            for name in names:
                if name in self.name_to_index:
                    idx = self.name_to_index[name]
                    if self.states[idx] == self.ROI_STATE_DELETED:
                        continue
                    self.states[idx] = self.ROI_STATE_SELECTED
                    if reason_of_selection:
                        self.reason_of_selection[idx] = reason_of_selection
                        #self.tags[idx].add(tag)

    def toggle(self, rois_or_names):
        """toggles the selction of the specified ROIs, preserving previous selections."""
        with self.lock:
            names = self._resolve_names(rois_or_names)
            for name in names:
                if name in self.name_to_index:
                    idx = self.name_to_index[name]
                    if self.states[idx] == self.ROI_STATE_DELETED:
                        IJ.log("oops! "+name+" already deleted")
                        continue
                    if self.states[idx] == self.ROI_STATE_ACTIVE:
                        self.states[idx] = self.ROI_STATE_SELECTED
                        self.reason_of_selection[idx] = "manual"
                    else:
                        self.states[idx] = self.ROI_STATE_ACTIVE
                        self.reason_of_selection[idx] = ""

    def add(self, rois):
        """Adds ROIs to the manager, setting their state to active."""
        with self.lock:
            for roi in rois:
                if roi:
                    name = roi.getName()
                    idx = self.name_to_index[name]
                    self.roi_array[idx] = roi
                    self.states[idx] = self.ROI_STATE_ACTIVE
                    self.tags[idx] = set()
                else:
                    IJ.log("Empty ROI encountered")

    def add_tuple(self, roi_state_tag_list):
        """Adds ROIs with associated state and tags."""
        with self.lock:
            for roi, state, tags in roi_state_tag_list:
                name = roi.getName()
                idx = self.name_to_index[name]
                self.roi_array[idx] = roi
                self.states[idx] = state
                self.tags[idx] = set(tags)

    def add_1_tuple(self, name_idx_roi_state_tag):
        """Adds  1 ROI with associated state and tags."""
        """trimmed version to be efficient."""
        #with self.lock:
        roi_name, idx,roi, state, tags= name_idx_roi_state_tag
        self.name_to_index[roi_name] = idx
        self.index_to_name[idx] = roi_name
        self.roi_array[idx] = roi
        self.states[idx] = state
        self.tags[idx] = set(tags)
        # create a TextRoi to show the name of the ROI on the image overlay
        stats = roi.getStatistics()
        x = int(stats.xCentroid)
        y = int(stats.yCentroid)
        label_roi = TextRoi(x, y + self.label_shift_y, roi_name)
        label_roi.setJustification(TextRoi.CENTER)
        label_roi.setColor(Color.WHITE)
        self.label_array[idx] = label_roi



    def delete(self, rois_or_names):
        """Marks the specified ROIs as deleted."""
        with self.lock:
            for name in self._resolve_names(rois_or_names):
                if name in self.name_to_index:
                    idx = self.name_to_index[name]
                    self.states[idx] = self.ROI_STATE_DELETED
                    if self.reason_of_selection[idx]:
                        self.tags[idx].add(self.reason_of_selection[idx])
                        self.reason_of_selection[idx]=""

    def change(self, rois_or_names, properties):
        """Modifies attributes of ROIs based on a property dictionary."""
        with self.lock:
            for name in self._resolve_names(rois_or_names):
                if name in self.name_to_index:
                    idx = self.name_to_index[name]
                    roi = self.roi_array[idx]
                    self.reason_of_selection[idx]="" 
                    for key, value in properties.items():
                        setattr(roi, key, value)

    def delete_selected(self,tag=None):
        """Marks all selected ROIs as deleted."""
        """Optionally adds a reason_of_selection or tag motivating the delete"""
        with self.lock:
                if tag:
                    IJ.log("delete_selected with tag: "+str(tag))
                    for idx, state in enumerate(self.states):
                        if state == self.ROI_STATE_SELECTED:
                            self.states[idx] = self.ROI_STATE_DELETED
                            self.tags[idx].add(tag)
                        self.reason_of_selection[idx]=""
                else:
                    for idx, state in enumerate(self.states):
                        if state == self.ROI_STATE_SELECTED:
                            self.states[idx] = self.ROI_STATE_DELETED
                            if self.reason_of_selection[idx]:
                                self.tags[idx].add(self.reason_of_selection[idx])
                                self.reason_of_selection[idx]=""    

    def get_state(self, name):
        """Returns the current state of the ROI with the given name."""
        with self.lock:
            idx = self.name_to_index.get(name)
            return self.states[idx] if idx is not None else None


    def get_roi(self, name):
        """Returns the ROI object associated with the given name."""
        with self.lock:
            idx = self.name_to_index.get(name)
            return self.roi_array[idx] if idx is not None else None

    def get_tuple(self, name):
        """Returns (roi, state, tags) tuple for the given ROI name."""
        with self.lock:
            idx = self.name_to_index.get(name)
            return (self.roi_array[idx], self.states[idx], self.tags[idx]) if idx is not None else None

    def __len__(self):
        """Returns the number of non-deleted ROIs."""
        with self.lock:
            return sum(1 for i in range(1, self.range_stop)
                       if self.roi_array[i] and self.states[i] != self.ROI_STATE_DELETED)

    def __iter__(self):
        """Iterator over all active (non-deleted) ROIs."""
        with self.lock:
            for i in range(1, self.range_stop):
                if self.roi_array[i] and self.states[i] != self.ROI_STATE_DELETED:
                    yield (self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i])

    def iter_all(self):
        """Iterator over all ROIs regardless of state."""
        with self.lock:
            for i in range(1, self.range_stop):
                if self.roi_array[i]:
                    yield (self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i])



    def map_over_rois(self, func):
        """Applies a function to all active (non-deleted) ROIs and returns a list of results."""
        with self.lock:
            return [func(self.roi_array[i]) for i in range(1, self.range_stop)
                    if self.roi_array[i] and self.states[i] != self.ROI_STATE_DELETED]

    def get_sample(self):
        """Returns the ROI at index 1 for quick inspection or testing."""
        return self.roi_array[1]

    def iter_by_state(self, target_state):
        """Iterator over ROIs matching the specified state."""
        with self.lock:
            for i in range(1, self.range_stop):
                if self.roi_array[i] and self.states[i] == target_state:
                    yield (self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i])
        
    # def select_by_filter(self, filterfn_idx, additive=False):
            # if additive:
                # for idx in range(1,self.range_stop):
                    # if self.states[idx]== self.ROI_STATE_DELETED:
                        # continue
                    # if filter_fn_idx(idx):
                        # self.states[idx] = self.ROI_STATE_SELECTED
            # else:
                # for idx in range(1,self.range_stop):
                    # if  self.states[idx]== self.ROI_STATE_DELETED:
                        # continue
                    # if filter_fn_idx(idx):
                        # self.states[idx] = self.ROI_STATE_SELECTED
                    # else:
                        # self.states[idx] = self.ROI_STATE_ACTIVE
                        
    # def iter_by_filter(self, filter_fn):
        # """Iterator over ROIs matching a custom filter function."""
        # with self.lock:
            # for i in range(1, self.range_stop):
                # if self.roi_array[i] and filter_fn(self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i]):
                    # yield (self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i])                        
    # def list_rois(self):
        # """Returns a list of all stored ROIs and their metadata."""
        # with self.lock:
            # return [(self.index_to_name[i], self.roi_array[i], self.states[i], self.tags[i])
                    # for i in range(1, self.range_stop) if self.roi_array[i] is not None]
    # def get_tags(self, name):
        # """Returns the tag set of the ROI with the given name."""
        # with self.lock:
            # idx = self.name_to_index.get(name)
            # return self.tags[idx] if idx is not None else set()

    # def set_tags(self, name, tags):
        # """Assigns a new tag set to the ROI with the given name."""
        # with self.lock:
            # idx = self.name_to_index.get(name)
            # if idx is not None:
                # self.tags[idx] = set(tags)


    # def set_state(self, rois_or_names, new_state):
        # """Sets a specific state to the specified ROIs."""
        # with self.lock:
            # for name in self._resolve_names(rois_or_names):
                # if name in self.name_to_index:
                    # idx = self.name_to_index[name]
                    # self.states[idx] = new_state

    # def get_all_names(self, exclude_deleted=False):
        # """Returns names of all ROIs, optionally excluding deleted ones."""
        # with self.lock:
            # return [name for name, idx in self.name_to_index.items()
                    # if self.roi_array[idx] is not None and (not exclude_deleted or self.states[idx] != self.ROI_STATE_DELETED)]
