"""
roi_image.py

Helper class to link an ImagePlus or ImageProcessor to a TinyRoiManager.
This class provides methods to visualize ROIs with color-coded overlays based on state
(e.g., active, selected, deleted) and to handle image visibility and optional window-closing hooks.

Author: Bart V.
Date: 2025-03-30
Version: 1.0
"""

from java.awt.event import WindowAdapter, WindowEvent
from java.awt import Color
from ij import IJ
from ij.gui import Overlay, TextRoi
from TinyRoiManager import TinyRoiManager


class RoiImage:
    """
    Manages an image (ImagePlus or ImageProcessor) in combination with a TinyRoiManager.
    Handles visualization of ROIs and custom interaction when the window is closed.
    """

    def __init__(self, image_or_processor, trm=None, on_window_closing=None):
        """
        Initialize the RoiImage with an image source and optional TinyRoiManager.

        Parameters:
        - image_or_processor: ImagePlus or ImageProcessor
        - trm: instance of TinyRoiManager (required)
        - on_window_closing: optional function to be called when image window is closed
        """
        if hasattr(image_or_processor, 'getProcessor'):
            self.image = image_or_processor
            self.processor = image_or_processor.getProcessor()
        else:
            self.image = None
            self.processor = image_or_processor

        if trm is None:
            raise ValueError("TinyRoiManager (trm) is required.")
        self.trm = trm

        # Default color and stroke-width styles per ROI state
        try:
            self.state_style_map = {
                TinyRoiManager.ROI_STATE_ACTIVE: (Color.YELLOW, 1.0),
                TinyRoiManager.ROI_STATE_DELETED: (Color.RED, 1.0),
                TinyRoiManager.ROI_STATE_SELECTED: (Color.BLUE, 5.0)
            }
        except:
            self.state_style_map = {}

        self.use_state_map = True
        self.visible = True

        if on_window_closing is not None and not callable(on_window_closing):
            raise ValueError("on_window_closing must be a callable.")
        self.on_window_closing = on_window_closing

    def set_state_map(self, state_map):
        """
        Set the style map for ROI states.

        Parameters:
        - state_map: dict mapping state (int) -> (Color, stroke width)
        """
        self.state_style_map = dict(state_map)

    def enable_state_map(self, flag):
        """
        Enable or disable usage of the state style mapping.

        Parameters:
        - flag: True to enable, False to disable
        """
        self.use_state_map = bool(flag)

    def show(self, overlay=True, show_labels=True, show_deleted=False):
        """
        Display the image with optional overlay of ROIs and labels.

        Parameters:
        - overlay: whether to apply an overlay of ROIs
        - show_labels: whether to show associated labels
        - show_deleted: whether to include deleted ROIs
        """
        if self.image is None:
            raise ValueError("No ImagePlus attached.")

        if overlay and self.trm:
            ov = Overlay()
            # Draw ROIs in consistent state order (deleted, active, selected)
            state_order = [
                TinyRoiManager.ROI_STATE_DELETED,
                TinyRoiManager.ROI_STATE_ACTIVE,
                TinyRoiManager.ROI_STATE_SELECTED
            ]

            for target_state in state_order:
                for name, roi, state, tags in self.trm.iter_all():
                    if state != target_state:
                        continue
                    if state == TinyRoiManager.ROI_STATE_DELETED and not show_deleted:
                        continue

                    if self.use_state_map:
                        if state in self.state_style_map:
                            color, stroke = self.state_style_map[state]
                        elif TinyRoiManager.ROI_STATE_ACTIVE in self.state_style_map:
                            color, stroke = self.state_style_map[TinyRoiManager.ROI_STATE_ACTIVE]
                        else:
                            color, stroke = (Color.magenta, 1.0)
                        roi.setStrokeColor(color)
                        roi.setStrokeWidth(stroke)

                    ov.add(roi)

                    if show_labels:
                        label = self.trm.label_array[self.trm.name_to_index[name]]
                        ov.add(label)

            self.image.setOverlay(ov)

        # Show the image window and attach optional close handler
        if self.image.getWindow() is None:
            self.image.show()
            if self.on_window_closing is not None:
                class Listener(WindowAdapter):
                    def windowClosing(inner_self, event):
                        self.on_window_closing()
                self.image.getWindow().addWindowListener(Listener())
            else:
                IJ.log("RoiImage: no on_window_closing callback provided")
        else:
            self.image.updateAndDraw()

    def setVisible(self, flag):
        """
        Set the visibility of the image window.

        Parameters:
        - flag: True to show, False to hide
        """
        self.visible = bool(flag)
        if self.image and self.image.getWindow():
            self.image.getWindow().setVisible(self.visible)

    def getProcessor(self):
        """Returns the underlying ImageProcessor."""
        return self.processor

    def getImage(self):
        """Returns the ImagePlus (if available), or None."""
        return self.image