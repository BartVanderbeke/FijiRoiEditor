# ✒ Fiji ROI Editor

**Fiji ROI Editor 1.0** is Fiji plugin for managing, editing, and analyzing Regions of Interest (ROIs) in image data. This Fiji Roi Editor is a derailed modification of the Fiji plug in [LabelsToRois](https://labelstorois.github.io/). The Fiji Roi Editor is implemented in Jython or Java-Python. The goal of RoiEditor is to remove “bad ROIs” from microscope images and to generate the data to perform statistics on the basic ROI properties: area and the Feret-parameters.
Fiji ROI Editor 1.0 has extended editing capabilities, but lacks the erosion and multiple slice functionality of the Fiji plugin [LabelsToRois](https://labelstorois.github.io/). 
Fiji RoiEditor cannot segment ROIs in photographs. [cellpose](https://www.cellpose.org/) is used for that purpose.

A standalone CPython-based twin of the Fiji RoiEditor, RoiEditor 2.0, is available too on [GitHub](https://github.com/BartVanderbeke/RoiEditor)

## ✨ Features
- when installed in Fiji, 'Edit ROIs' will appear deep down on the list of plug ins.
- The original photograph is loaded from a .png or .tif(f) file.
- The cellpose label-data can be read from a .png file.
- The ROIs are stored in and read back from a Fiji compatible ROI zip file.
- The measurements are collected in a dedicated class, not using Fiji's table.
- The ROIs are stored in a simple and lean TinyRoiManager.
- Contrary to most ROI-handling apps or plug ins, RoiEditor never removes ROIs from the collection:
  Deleted ROIs are marked, but not removed.
- The state data and other metadata is stored in a json file in the ROI zip file.
- Area & Feret measurements are computed for all ROIs, not using Fiji's measurement table.git add
- The stats for each measurement are shown in a histogram window.
- The user can select the edge of the ROI-cloud or the outliers for each measurement for deletion.
- An outlier for a measurement is a value deviating more than 1.5 * IQR from the median.
- The measurements are written to a .csv file.

## 🧮 Workflow
The plot below shows the integrated workflow using [cellpose](https://www.cellpose.org/) and RoiEditor.<br>
<img src=".\fiji.app\assets\FijiRoiEditorWorkflow.svg" alt="cellpose and Fiji RoiEditor integrated workflow" width="400"/><br>
Compared to RoiEditor 2.0 the Fiji ROI Editor 1.0 lacks the export of measurements to an xlsx file and the overlay with the ROIs colored according to their distance to to the median of the selected meaesurement.
