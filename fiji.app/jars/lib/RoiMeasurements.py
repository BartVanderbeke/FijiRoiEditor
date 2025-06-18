"""

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
"""

import math
import os
import threading
from ij import IJ

from javax.swing import JTable, JScrollPane, JFrame
from javax.swing.table import DefaultTableModel
from java.awt import Toolkit
from format import format_number

from RoiHistogram import RoiHistogram
from HistogramPlotFrame import HistogramPlotFrame
from TinyRoiManager import TinyRoiManager as RoiManager


import time
import os

def get_timestamp_string():
    """Return current time as a string in yyyymmddHHMMSS format."""
    return time.strftime("%Y%m%d%H%M%S")

class RoiMeasurements:
    """
    Class to compute and store multiple measurements (e.g., Area, Feret, FeretAngle, etc.)
    for a list of ROI objects in a compact matrix structure.

    Upon construction, this class:
    - Computes all specified measurements for each ROI
    - Stores both raw values and squared values for fast statistical analysis
    - Computes mean and standard deviation per measurement across all ROIs in a single pass
    """
    
    def __init__(self,gvars):


        self.measurement_names=["Area","Feret", "FeretAngle", "MinFeret", "FeretX", "FeretY"]
        self.measurement_names_wo_area =["Feret", "FeretAngle", "MinFeret", "FeretX", "FeretY"]
        self.measurements = {}
        self.squared_measurements = {}
        self.roi_subset = {} # dict "subset_name" -->  1 roi_sub_set
        self.subset_stats = {} # dict "subset_name" --> 1 sub_set_stats
        self.Initialized = False
        self.RecalculateWorker =None
        self.outliers= {}
        self.gvars=gvars
        self.gvars["Measurements"]=self

    def compute_measurements_all(self):

        rm = RoiManager.getInstance2()
        self.roi_subset["ALL"] = []

        self.Initialized = False
        self.measurements = {}

        self.subset_stats = {}      # dict [subset_name][msmt_name] --> 1 sub_set_stats
        self.squared_measurements = {} # [roi_name][msmt_name]
        subset_name = "ALL"
        N = 0
        self.subset_stats[subset_name] = {
            msmt_name: {
                "N": 0,
                "Average": 0.0,
                "Stdev": 0.0,
                "Min": float('inf'),
                "Max": float('-inf'),
                "Median": 0.0,
                "Q1": 0.0,
                "Q3": 0.0,
                "MAD": 0.0,
                "num_outliers": "--"
            } for msmt_name in self.measurement_names
        }
        stat = self.subset_stats[subset_name]

        raw_values = {msmt_name: [] for msmt_name in self.measurement_names}

        for N, (roi_name, roi, state, tags) in enumerate(rm.iter_all()):
            msmt = {}
            squared = {}

            msmt_name = "Area"
            roi_stats = roi.getStatistics()
            val = roi_stats.area
            msmt[msmt_name] = val
            val2 = val * val
            squared["Area"] = val2
            _stat = stat[msmt_name]

            _stat["Average"] += val
            _stat["Stdev"] += val2
            _stat["Min"] = _stat["Min"] if _stat["Min"] <= val else val
            _stat["Max"] = _stat["Max"] if _stat["Max"] >= val else val
            raw_values[msmt_name].append(val)

            feret_values = roi.getFeretValues()
            msmt_names = self.measurement_names_wo_area
            for i, msmt_name in enumerate(msmt_names):
                val = feret_values[i]
                val2 = val * val
                msmt[msmt_name] = val
                squared[msmt_name] = val2
                _stat = stat[msmt_name]
                _stat["Average"] += val
                _stat["Stdev"] += val2
                _stat["Min"] = _stat["Min"] if _stat["Min"] <= val else val
                _stat["Max"] = _stat["Max"] if _stat["Max"] >= val else val
                raw_values[msmt_name].append(val)

            self.measurements[roi_name] = msmt
            self.squared_measurements[roi_name] = squared
            self.roi_subset["ALL"].append(roi_name)

        N = N + 1 if N >= 0 else 1
        N_minus_1 = N - 1 if N > 1 else 1

        for msmt_name in self.measurement_names:
            _stat = stat[msmt_name]
            sum_x = _stat["Average"]
            sum_x2 = _stat["Stdev"]
            mean = sum_x / N
            variance = (sum_x2 - (sum_x * sum_x / N)) / N_minus_1
            _stat["Average"] = mean
            _stat["Stdev"] = math.sqrt(variance)
            _stat["N"] = N

            values = sorted(raw_values[msmt_name])
            def median(lst, start, end):
                count = end - start
                mid = start + count // 2
                if count % 2 == 1:
                    return lst[mid]
                else:
                    return 0.5 * (lst[mid - 1] + lst[mid])

            med = median(values, 0, N)
            q1 = median(values, 0, N // 2)
            q3 = median(values, (N + 1) // 2, N)
            mad = median(sorted([abs(x - med) for x in values]), 0, N)

            _stat["Median"] = med
            _stat["Q1"] = q1
            _stat["Q3"] = q3
            _stat["MAD"] = mad
            _stat["num_outliers"]= "--"
            # MAD (median absolute deviation)
            # https://en.wikipedia.org/wiki/Median_absolute_deviation
        
       
        self.Initialized=True

    def compute_measurements_subset(self, subset_name, roi_subset_names):
        if not self.Initialized:
            IJ.log("RoiMeasurements: Measurements not initialised")
            return

        if roi_subset_names:
            self.subset_stats[subset_name] = {
                msmt_name: {
                    "N": 0,
                    "Average": 0.0,
                    "Stdev": 0.0,
                    "Min": float('inf'),
                    "Max": float('-inf'),
                    "Median": 0.0,
                    "Q1": 0.0,
                    "Q3": 0.0,
                    "MAD": 0.0,
                    "num_outliers": 0
                } for msmt_name in self.measurement_names
            }
        else:
            self.subset_stats[subset_name] = {
                msmt_name: {
                    "N": 0,
                    "Average": 0.0,
                    "Stdev": 0.0,
                    "Min": 0.0,
                    "Max": 0.0,
                    "Q1": 0.0,
                    "Q3": 0.0,
                    "MAD": 0.0,
                    "num_outliers": 0
                } for msmt_name in self.measurement_names
            }
            self.roi_subset[subset_name] = []
            return

        self.roi_subset[subset_name] = roi_subset_names

        # Verzamel ruwe waarden voor robuuste statistiek
        if not hasattr(self, "_subset_raw_values"):
            self._subset_raw_values = {}
        self._subset_raw_values[subset_name] = {
            msmt_name: [] for msmt_name in self.measurement_names
        }

        for roi_name in self.roi_subset[subset_name]:
            stat = self.subset_stats[subset_name]
            if roi_name in self.measurements:
                measurements = self.measurements[roi_name]
            else:
                IJ.log("Subset computation failed on ROI: " + roi_name)
                raise KeyError

            squared_measurements = self.squared_measurements[roi_name]

            for msmt_name in self.measurement_names:
                val = measurements[msmt_name]
                val2 = squared_measurements[msmt_name]
                _stat = stat[msmt_name]
                _stat["Average"] += val
                _stat["Stdev"] += val2
                _stat["Min"] = _stat["Min"] if _stat["Min"] <= val else val
                _stat["Max"] = _stat["Max"] if _stat["Max"] >= val else val
                self._subset_raw_values[subset_name][msmt_name].append(val)

        l = len(self.roi_subset[subset_name])
        N = l if l > 0 else 1
        N_minus_1 = N - 1 if N > 1 else 1

        # Turn the sums (of squares) into actual stats
        for msmt_name in self.measurement_names:
            stat = self.subset_stats[subset_name]
            _stat = stat[msmt_name]

            sum_x = _stat["Average"]
            sum_x2 = _stat["Stdev"]
            mean = sum_x / N

            variance = (sum_x2 - (sum_x * sum_x / N)) / N_minus_1
            _stat["Average"] = mean
            _stat["Stdev"] = math.sqrt(variance)
            _stat["N"] = N

            # Robust statistics (median, Q1, Q3, MAD)
            values = self._subset_raw_values[subset_name][msmt_name]
            if values:
                sorted_values = sorted(values)
                def median(lst, start, end):
                    count = end - start
                    mid = start + count // 2
                    if count % 2 == 1:
                        return lst[mid]
                    else:
                        return 0.5 * (lst[mid - 1] + lst[mid])

                med = median(sorted_values, 0, N)
                q1 = median(sorted_values, 0, N // 2)
                q3 = median(sorted_values, (N + 1) // 2, N)
                mad = median(sorted([abs(x - med) for x in sorted_values]), 0, N)

                _stat["Median"] = med
                _stat["Q1"] = q1
                _stat["Q3"] = q3
                _stat["MAD"] = mad

        #subset_name = "ACTIVE"
        self.outliers[subset_name]= {}
        stat = self.subset_stats[subset_name]
        for msmt_name in self.measurement_names:
            _stat = stat[msmt_name]
            iqr = _stat["Q3"]- _stat["Q1"]
            median = _stat["Median"]
            upper_limit = median + 1.5 * iqr
            lower_limit = median - 1.5 * iqr
            rois_in_subset =  self.roi_subset[subset_name]
            self.outliers[subset_name][msmt_name]=[]
            for roi_name in rois_in_subset:
                val = self.measurements[roi_name][msmt_name]
                if val < lower_limit or val > upper_limit:
                    self.outliers[subset_name][msmt_name].append(roi_name)
            _stat["num_outliers"]=len(self.outliers[subset_name][msmt_name])

        
        
    def save_all(self, full_path):
        rm = RoiManager.getInstance2()
        all_but_ext, _ = os.path.splitext(full_path)
        now=get_timestamp_string()
        msmts_folder = os.path.dirname(all_but_ext)+"/Msmts/"
        filename_wo_ext = os.path.basename(all_but_ext)
        if not os.path.exists(msmts_folder):
            os.makedirs(msmts_folder)
            IJ.log("Create folder for measurements: "+msmts_folder)
        full_name = msmts_folder + now + "_" + filename_wo_ext+".csv"
        with open(full_name, 'w') as f:
            header = ['name'] + self.measurement_names + ["STATE"]+["TAGS"] 
            f.write(';'.join(header) + '\n')
            for roi_name in self.measurements:
                (_, state, tags) = rm.get_tuple(roi_name)
                roi_state_str = RoiManager.state_to_str(state)
                roi_tag_str = ', '.join(tags)
                row = [roi_name] + [format_number(self.measurements[roi_name][name]) for name in self.measurement_names] + [roi_state_str]+ [roi_tag_str]
                f.write(';'.join(row) + '\n')
        IJ.log("Measurements written to : "+full_name)

    def save_subset(self, subset_name, full_path):

        roi_subset=self.roi_subset[subset_name]
        with open(full_path, 'w') as f:
            header = ['name'] + self.measurement_names
            f.write(','.join(header) + '\n')
            for roi in roi_subset:
                roi_name = roi.getName()
                row = [roi_name] + [str(self.measurements[roi_name][name]) for name in self.measurement_names]
                f.write(','.join(row) + '\n')

    def get_stats_subset(self, subset_name, measurement_name):
        stat = self.subset_stats[subset_name][measurement_name]
        return stat["Average"], stat["Stdev"]
        
    def data_have_changed(self,caller=None):
        self.RecalculateWorker.execute()
       
# === Background workers defined apart from RoiMeasurements ===
"""
Usage of background workers:
names = ["Feret", "FeretAngle", "MinFeret", "FeretX", "FeretY"]

msmts = RoiMeasurements(roi_list, measurements)

# Start background computation of all measurements:
worker = ComputeAllWorker(msmts)
worker.execute()

# Start background computation of subset statistics:
worker = ComputeSubsetWorker(msmts, roi_subset)
worker.execute()

# Then use:
worker = MyWorker(msmts,gvars)
worker.execute()
"""

import datetime
from javax.swing import SwingWorker
from StopWatch import StopWatch

class ComputeAllWorker(SwingWorker):
    def __init__(self,msmts,gvars,continuation=None):
        SwingWorker.__init__(self)
        self.msmts = msmts
        self.gvars=gvars
        self.continuation=continuation
    
    def doInBackground(self, continuation=None):
        StopWatch().start("")
        self.msmts.compute_measurements_all()
        rm = RoiManager.getInstance2()

        roi_subset=[name for (name, roi, state, tags) in rm.iter_by_state(RoiManager.ROI_STATE_ACTIVE)]
        self.msmts.compute_measurements_subset("ACTIVE", roi_subset)

        roi_subset=[name for (name, roi, state, tags) in rm.iter_by_state(RoiManager.ROI_STATE_DELETED)]

        self.msmts.compute_measurements_subset("DELETED", roi_subset)

    def done(self):
        StopWatch().stop("Computing measurements")
        
        self.msmts.save_all(self.gvars['path_original_image'])
        
        if callable(self.continuation):
            self.continuation()
                
        worker = ComputeHistAllWorker(self.msmts,self.gvars,continuation=None)
        worker.execute()
        
class ComputeHistAllWorker(SwingWorker):
    def __init__(self,msmts,gvars, continuation=None):
        SwingWorker.__init__(self)
        self.start_time=None
        self.end_time=None
        self.msmts = msmts
        self.gvars =gvars
        self.hist_data = RoiHistogram(num_bins=19, num_x_values=200, roi_measurements=self.msmts)
        self.continuation=continuation
    
    def doInBackground(self):
        StopWatch().start("")
        self.hist_data.compute()

    def done(self):
        StopWatch().stop("Computing histogram")
        
        frmHist = HistogramPlotFrame(roi_histogram_data=self.hist_data, initial_measurement_name="Feret", gvars=self.gvars)
        frmHist.show_plot()
        
        self.msmts.RecalculateWorker=RecalculateWorker(frmHist,self.msmts,self.hist_data)
        
        if callable(self.continuation):
            self.continuation()


import datetime
from javax.swing import SwingWorker
from ij import IJ
from TinyRoiManager import TinyRoiManager as RoiManager

class RecalculateWorker():
    def __init__(self, frmHist, msmts, hist_data):
        self.frmHist = frmHist
        self.msmts = msmts
        self.hist_data = hist_data

    def execute(self):
        worker = self.EmbeddedRecalculateWorker(self.frmHist, self.msmts, self.hist_data)
        worker.execute()

    class EmbeddedRecalculateWorker(SwingWorker):

        def __init__(self, frmHist, msmts, hist_data):
            SwingWorker.__init__(self)
            self.frmHist = frmHist
            self.msmts = msmts
            self.hist_data = hist_data

        def doInBackground(self):
            rm = RoiManager.getInstance2()
            StopWatch().start()
            self.start_time = datetime.datetime.now()

            roi_subset = [name for (name, roi, state, tags) in rm.iter_by_state(RoiManager.ROI_STATE_ACTIVE)]
            self.msmts.compute_measurements_subset("ACTIVE", roi_subset)
            
            roi_subset = [name for (name, roi, state, tags) in rm.iter_by_state(RoiManager.ROI_STATE_DELETED)]
            self.msmts.compute_measurements_subset("DELETED", roi_subset)

            self.hist_data.compute()

        def done(self):
        
            StopWatch().stop("Recomputing histograms")

            self.frmHist.show_plot()
