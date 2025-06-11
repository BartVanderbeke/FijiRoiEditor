"""

HistogramPlotFrame.py


Description:
This class displays histogram plots of measurements on ROI subsets.
The GUI provides a dropdown to select measurements and shows a combined
visualization of histograms, median/stdev lines, and a statistics table.
Data is processed using a background thread (SwingWorker) and displayed in
a JFrame with JSplitPane.

External dependencies:
  - org.knowm.xchart for chart plotting
  - javax.swing for GUI components
  - ij.IJ for logging
  - format.format_number for formatted numerical output

"""
from org.knowm.xchart import XYChart, XYChartBuilder, XChartPanel, XYSeries
from org.knowm.xchart.style.markers import None as NoMarker, Plus, Cross
from java.awt import Color, BorderLayout, Toolkit
from javax.swing import JFrame, JTable, JSplitPane, JPanel, JComboBox, JButton, SwingWorker
from javax.swing.table import DefaultTableModel
from ij import IJ
from format import format_number

class ColorCycler(object):
    def __init__(self):
        self.colors = [Color.BLUE, Color.GREEN, Color.RED, Color.MAGENTA, Color.ORANGE, Color.PINK, Color.BLACK]
        self.index = 0

    def next(self):
        color = self.colors[self.index]
        self.index = (self.index + 1) % len(self.colors)
        return color

class HistogramPlotFrame:
    def __init__(self, roi_histogram_data, initial_measurement_name, gvars, title=None):
        self.headers = ["roi set", "N", "average", "stdev", "median", "MAD", "IQR","Outliers"]
        self.histogram_data = roi_histogram_data
        self.selected_measurement_name = initial_measurement_name
        self.msmts = self.histogram_data.roi_measurements
        self.measurement_names = self.histogram_data.roi_measurements.measurement_names #msmts.measurement_names
        self.frame = None
        self.split_pane = None
        self.dropdown = None
        self.content_panel = None
        self.first_time = True
        self.next_color = None
        self.gvars=gvars
        self.gvars["selected_measurement_name"]=self.selected_measurement_name

    def on_select_measurement(self, event):
        selected = str(self.dropdown.getSelectedItem())
        IJ.log("Selected measurement:" + selected)
        if selected != self.selected_measurement_name:
            IJ.log("Selected different measurement:" + selected)
            self.selected_measurement_name = selected
            self.gvars["selected_measurement_name"]=self.selected_measurement_name
            self.show_plot()

    # def on_refresh(self, event):
        # #self.gvars["Measurements"].RecalculateWorker.execute()
        # self.gvars["Measurements"].data_have_changed("delete_key")

    def show_plot(self):
        self.next_color = ColorCycler().next
        if self.selected_measurement_name not in self.histogram_data.plot_data['ALL']:
            raise ValueError("No histogram data for measurement: " + self.selected_measurement_name)

        self.title = "Histogram: " + self.selected_measurement_name

        if self.first_time:
            self.frame = JFrame(self.title)
            self.frame.setVisible(False)

            self.dropdown = JComboBox(self.measurement_names)
            self.dropdown.setSelectedItem(self.selected_measurement_name)
            self.dropdown.addActionListener(self.on_select_measurement)

            self.content_panel = JPanel(BorderLayout())
            self.content_panel.add(self.dropdown, BorderLayout.NORTH)
            self.frame.setContentPane(self.content_panel)

            self.frame.pack()
            self.frame.setSize(600, 600)
            screenSize = Toolkit.getDefaultToolkit().getScreenSize()
            self.frame.setLocation(screenSize.width - self.frame.getSize().width, 0)

            
            self.first_time = False
        else:
            self.frame.setTitle(self.title)

        worker = self.GenerateSeriesWorker(self)
        worker.execute()


    def dispose(self):
        if self.frame:
            self.frame.dispose()
            self.frame = None

    class GenerateSeriesWorker(SwingWorker):
        def __init__(self, outer):
            self.outer = outer
            self.result = None

        def doInBackground(self):
            chart = XYChartBuilder().width(600).height(400).title(self.outer.title).xAxisTitle(self.outer.selected_measurement_name).yAxisTitle("Frequency").build()
            styler = chart.getStyler()
            styler.setLegendVisible(True)

            bin_start = self.outer.histogram_data.bin_start[self.outer.selected_measurement_name]
            edges_y = [0 for _ in bin_start]
            bin_edges_series = chart.addSeries("bin_edges", bin_start, edges_y)
            bin_edges_series.setLineWidth(0.001)
            bin_edges_series.setMarker(Plus())
            bin_edges_series.setShowInLegend(False)
            bin_edges_series.setMarkerColor(Color.LIGHT_GRAY)
            bin_edges_series.setLineColor(Color.LIGHT_GRAY)

            table_data = [self.outer.headers]
            next_color = self.outer.next_color
            for subset_name in self.outer.histogram_data.plot_data.keys():
                stats = self.outer.msmts.subset_stats[subset_name][self.outer.selected_measurement_name]
                N = stats["N"]
                x_average = stats["Average"]
                stdev = stats["Stdev"]
                if stats["N"] ==0:
                    median_x=0
                    table_data.append([subset_name, str(N), format_number(x_average), format_number(stdev), format_number(median_x), 0.0, 0.0, 0])
                    continue
                xMin = stats["Min"]
                xMax = stats["Max"]


                hist_data = self.outer.histogram_data
                plot_data = hist_data.plot_data[subset_name][self.outer.selected_measurement_name]
                x = plot_data["x"]
                y = plot_data["y"]
                yMax = hist_data.yMax[subset_name][self.outer.selected_measurement_name]
                yMin = hist_data.yMin[subset_name][self.outer.selected_measurement_name]
                median_x = stats["Median"]
                iqr = stats["Q3"]-stats["Q1"]
                mad = stats["MAD"]
                mid_y = (yMin + yMax) / 2
                upper_limit = median_x + 1.5 * iqr
                lower_limit =median_x - 1.5 * iqr
                x_average_minus_stdev= x_average - stdev
                num_outliers=stats["num_outliers"]

                table_data.append([subset_name, str(N), format_number(x_average), format_number(stdev), format_number(median_x),format_number(mad),format_number(iqr), str(num_outliers)])

                line_width = { 'ACTIVE': { "thick" : 1.5, "thinner" : 0.5, "thinnest" : 0.2},
                               'DELETED': { "thick" : 0.5, "thinner" : 0.1, "thinnest" : 0.05},
                               'ALL': { "thick" : 0.5, "thinner" : 0.1, "thinnest" : 0.05}
                }
                _l= line_width[subset_name]
                color = next_color()
                series_package = {
                    self.outer.selected_measurement_name: {"x_data": x, "y_data": y, "color": color, "line_width": _l["thick"], "marker": NoMarker(), "in_legend": True},
                    "avg_vline": {"x_data": [x_average, x_average], "y_data": [yMin, yMax], "color": color, "line_width": _l["thinner"], "marker": Plus(), "in_legend": False},
                    "median_vline": {"x_data": [median_x, median_x], "y_data": [yMin, yMax], "color": color, "line_width": _l["thinner"], "marker": Cross(), "in_legend": False},
                    "upper_limit_vline": {"x_data": [upper_limit, upper_limit], "y_data": [yMin, yMax], "color": color, "line_width": _l["thinnest"], "marker": Cross(), "in_legend": False}
                }
                if x_average_minus_stdev >=0:
                    series_package["std_points"]={"x_data": [x_average_minus_stdev, x_average, x_average + stdev], "y_data": [mid_y, mid_y, mid_y], "color": color, "line_width": _l["thinnest"], "marker": Plus(), "in_legend": False}
                    series_package["std_hline"]={"x_data": [x_average_minus_stdev, x_average + stdev], "y_data": [mid_y, mid_y], "color": color, "line_width": _l["thinnest"], "marker": NoMarker(), "in_legend": False}
                else:
                    series_package["std_points"]={"x_data": [x_average, x_average + stdev], "y_data": [mid_y, mid_y], "color": color, "line_width": _l["thinnest"], "marker": Plus(), "in_legend": False}
                    series_package["std_hline"] ={"x_data": [x_average, x_average + stdev], "y_data": [mid_y, mid_y], "color": color, "line_width": _l["thinnest"], "marker": NoMarker(), "in_legend": False}
                    
                if lower_limit>0:
                    series_package["lower_limit_vline"]={"x_data": [lower_limit, lower_limit], "y_data": [yMin, yMax], "color": color, "line_width": _l["thinnest"], "marker": Cross(), "in_legend": False}


                for srs_name, data in series_package.items():
                    unique_name = subset_name + "." + srs_name
                    s = chart.addSeries(unique_name, data["x_data"], data["y_data"])
                    s.setLineWidth(data["line_width"])
                    s.setLineColor(data["color"])
                    s.setMarker(data["marker"])
                    s.setMarkerColor(data["color"])
                    s.setShowInLegend(data["in_legend"])

            table_model = DefaultTableModel(table_data, self.outer.headers)
            chart_panel = XChartPanel(chart)
            table_panel = JPanel(BorderLayout())
            table = JTable(table_model)
            table_panel.add(table, BorderLayout.CENTER)

            split_pane = JSplitPane(JSplitPane.VERTICAL_SPLIT)
            split_pane.setTopComponent(chart_panel)
            split_pane.setBottomComponent(table_panel)
            split_pane.setResizeWeight(1.0)

            self.result = (split_pane, chart_panel, table)
            return self.result

        def done(self):
            try:
                result = self.get()
                if result is None:
                    return
                # Dispose old components to free memory
                me = self.outer
                if me.split_pane is not None:
                    old_top = me.split_pane.getTopComponent()
                    old_bottom = me.split_pane.getBottomComponent()
                    if old_top is not None:
                        old_top.removeAll()
                        old_top.revalidate()
                        old_top.repaint()
                    if old_bottom is not None:
                        old_bottom.removeAll()
                        old_bottom.revalidate()
                        old_bottom.repaint()
                    me.split_pane.removeAll()
                    me.split_pane.revalidate()
                    me.split_pane.repaint()

                split_pane, chart_panel, table = result
                if me.split_pane:
                    me.content_panel.remove(me.split_pane)
                me.split_pane = split_pane
                me.content_panel.add(me.split_pane, BorderLayout.CENTER)
                me.content_panel.revalidate()
                me.content_panel.repaint()
                me.frame.setSize(600, 600)
                me.frame.setVisible(True)
            except Exception as e:
                IJ.log("Error in GenerateSeriesWorker.done: " + str(e))
