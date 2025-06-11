"""
Edit_Rois.py

Edit_Rois is based on https://labelstorois.github.io/
The multiple file capability and the Eroding have been removed.
The editing capability has been extended
- when reading label files from Cellpose, each roi derived from a label gets a name associated with the label number
  label n is named Lnnnn
- ROIs are never deleted from the collection, they have a state and that state determines how they are handled
- ROIs can have the state ACTIVE, SELECTED or DELETED
- When saving ROIs, the state of the rois is stored into the zip as jason file
- A new tiny RoiManager, TinyRoiManager has been created that has no UI, but is faster than the quite fat Fiji RoiManager
- The computations are not used, a dedicated RoiMeasurements class has been created
- Most calculations have been moved to threads or backgroundworkers so the Fiji UI never freezes
- Multiple selection is possible
- Single clicking an ROI toggles the selction of an ROI
- Alt single click deletes the clicked ROI
- The DELETE key deletes all selected ROIs
- The ESCAPE key deselects all selected ROIs
- Hold and drag with the mouse, creates a rectangle on the image, F1 selects all ROIs that are inside the rectangle
- A figure is created that shows the statistics of 'ALL','DELETED' and 'ACTIVE' ROIs
  This allows assessing the impact of the deleting ROIs on the statistics
- The plugin always requires a label image to be opened
- when converting a label image to ROIs, small ROIs can be removed automatically
- when converting a label image to ROIs, ROIs at thedge of the image can be removed automatically
- when loading an ROI file, small ROIs can be removed automatically
- when loading an ROI file, ROIs at the edge of the image can be removed automatically


- the file 'Labels_To_Rois.py' must be stored in Fiji's plugin folder
- the other files must be stored in jars/lib

"""
__license__ = "MIT"
__email__ = "bart.vanderbeke@gmail.com"
__author__ = "Bart Vanderbeke"
__date__ = "2025-03-30"
__version__ = "1.0"

from EditRoisGo import just_go_for_it
just_go_for_it()