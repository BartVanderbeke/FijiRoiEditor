class RoiHistogram:
    """
    Class to compute histogram data for all measurements from a RoiMeasurements object.
    This class prepares all data in the background to allow the plot to be hson or updated instantaneously
    Each bin contains a list of ROI names that fall into that bin (not just a count).
    Also computes oversampled x and y values for plotting.

    Usage:
        hist = RoiHistogram(num_bins=20, num_x_values=200, measurements=msmts)
        hist.compute()
        result = hist.bins["Area"]  # list of bins for 'Area', each bin = list of ROI names
        plot_x = hist.plot_data["Area"]["x"]
        plot_y = hist.plot_data["Area"]["y"]
    """
    def __init__(self, num_bins, num_x_values, roi_measurements):
        self.num_bins = num_bins
        self.num_x_values = num_x_values
        self.roi_measurements = roi_measurements
        self.bins = {}       # {measurement_name: list of bins, each bin = list of ROI names}
        self.plot_data = {}  # {measurement_name: {"x": [...], "y": [...], "bin_edges": [...]}}
        self.bin_width = {}
        self.x_range = {}
        self.bin_start = {}
        self.yMax = {}
        self.yMin = {}
    def compute(self):
        self.bins = {}       # {measurement_name: list of bins, each bin = list of ROI names}
        self.plot_data = {}  # {measurement_name: {"x": [...], "y": [...], "bin_edges": [...]}}
        self.bin_width = {}
        self.x_range = {}
        self.bin_start = {}
        self.yMax = {}
        self.yMin = {}

        for msmt_name in self.roi_measurements.measurement_names:
            # the plot parameters (a.o. bin widths & edges)are shared amongst all sub_sets of 1 measurement
            subset_name = "ALL"
            minval = self.roi_measurements.subset_stats[subset_name][msmt_name]["Min"]
            maxval = self.roi_measurements.subset_stats[subset_name][msmt_name]["Max"]
            x_range = (maxval - minval)
            self.x_range[msmt_name]=x_range
            bin_width = x_range / float(self.num_bins)
            self.bin_width[msmt_name] = bin_width
            
            self.bin_start[msmt_name] =[ minval+(i * bin_width) for i in range(self.num_bins+1)]
            
            x_step = x_range / float (self.num_x_values)
            bin_idx_step = float(self.num_bins) / float(self.num_x_values)
            subset_names=self.roi_measurements.subset_stats.keys()

            for subset_name in subset_names:
                # Prepare empty bins
                self.bins.setdefault(subset_name, {})[msmt_name] = [[] for _ in range(self.num_bins)]

                roi_names = self.roi_measurements.roi_subset[subset_name]

                for roi_name in roi_names:
                    val = self.roi_measurements.measurements[roi_name][msmt_name]
                    bin_index = int((val - minval) / bin_width)
                    bin_index = min(self.num_bins - 1, bin_index)
                    self.bins[subset_name][msmt_name][bin_index].append(roi_name)

                # Oversampled plotting data
                x_plot = []
                y_plot = []
                # x_step is no longer needed here due to bin_idx_step usage
                x_val = minval
                bin_idx_float = 0.0

                for x_idx in range(self.num_x_values + 1):
                    # oversampled bin index stepping (avoiding repeated multiplies)
                    bin_idx_float += bin_idx_step
                    bin_idx = int(bin_idx_float)
                    bin_idx = min(self.num_bins - 1, bin_idx)
                    x_val +=  x_step
                    x_plot.append(x_val)
                    bin_content = self.bins[subset_name][msmt_name][bin_idx]
                    frequency = len(bin_content)
                    y_plot.append(frequency)

                self.plot_data.setdefault(subset_name, {})[msmt_name] = {"x": x_plot, "y": y_plot}
                self.yMax.setdefault(subset_name, {})[msmt_name] = max(y_plot) * 1.01
                self.yMin.setdefault(subset_name, {})[msmt_name] = min(y_plot)

                
             
from javax.swing import SwingWorker

class ComputeHistogramDataWorker(SwingWorker):
    """
    Background worker to compute histogram bin data using RoiHistogram.

    Usage:
        worker = ComputeHistogramDataWorker(histogram)
        worker.execute()

        # override done() in subclass for custom handling
    """
    def __init__(self, histogram):
        SwingWorker.__init__(self)
        self.histogram = histogram

    def doInBackground(self):
        self.histogram.compute()

    def done(self):
        # Override or extend this method
        pass
