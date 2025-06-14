from ij import IJ
#from ij.plugin.frame import RoiManager
from java.awt.event import MouseAdapter
from TinyRoiManager import TinyRoiManager as RoiManager
#from RoiImage import RoiImage

class ROIClickListener(MouseAdapter):
    """
      no special keys pressed, single click (left) on ROI --> toggle selection
      Alt + double click (left) on ROI, no other special keys pressed --> delete clicked ROI

    """
    def __init__(self, roi_image, label_imp, gvars):
        self.valid = True

        self.roi_image = roi_image
        self.frame = roi_image.frame
        self.panel = roi_image.panel

        self.label_imp = label_imp
        self.label_pixels = label_imp.getProcessor().getPixels()
        self.width = label_imp.getWidth()

        self.rm = RoiManager.getInstance2()
        self.gvars = gvars
        self.name_digits = self.rm.name_length - 1
        
        if self.rm is None:
            IJ.log("Mouse: ROI Manager must be open!")
            self.valid = False

    def mouseClicked(self, event):
        if event.getClickCount() != 1 or event.isControlDown() or event.isShiftDown() or event.getButton() != event.BUTTON1:
            IJ.log("Mouse clicked, but no click to act on")
            return
        # invariant : 1 click and  (ctrl and shift NOT pressed) and (left button clicked)
        alt = event.isAltDown()
        toggle_selection = not (alt)
        delete_clicked = alt
        x_panel = event.getX()
        y_panel = event.getY()
        x, y = self.roi_image.panel.panelToImageCoordinates(x_panel, y_panel)
        # x = event.getX()
        # y = event.getY()
        if not (0 <= x < self.width and 0 <= y < self.label_imp.getHeight()):
            IJ.log("Mouse clicked outside of image")
            return
        idx = int(y) * self.width + int(x)
        label_val = int(self.label_pixels[idx])
        
        if label_val <= 0:
            return
        roi_name = "L" + str(label_val).zfill(self.name_digits)
        roi = self.rm.get_roi(roi_name)
        if not roi:
            IJ.log("Mouse clicked, but no ROI associated with this location")
            return
        state = self.rm.get_state(roi_name)
        if state == RoiManager.ROI_STATE_DELETED:
            return
      
        # no special keys pressed, single click (left) on ROI --> toggle select
        if toggle_selection:
            self.rm.toggle(roi_name)

        # Alt + single click (left), no other special keys pressed --> delete clicked ROI
        else: # invariant: delete_clicked
            self.rm.delete(roi)

            self.gvars["Measurements"].data_have_changed("delete_button_clicked")
  
        self.roi_image.show(overlay=True,show_labels=self.gvars["show_names"],show_deleted=self.gvars["show_deleted"])


    def activate(self):
        if self.valid:
            self.panel.addMouseListener(self)
        else:
            IJ.log("Cannot activate mouse listener")

    def deactivate(self):
        self.panel.removeMouseListener(self)

    def dispose(self):
        self.deactivate()
        self.label_pixels = None
        self.rm = None
        self.valid = False