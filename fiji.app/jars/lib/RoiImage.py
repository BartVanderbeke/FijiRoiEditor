"""
roi_image_swing.py

Swing-based version of RoiImage with dynamic scaling and zoom support.
Uses Java Swing windowing to visualize ImageProcessor content with ROI overlays.
Compatible with TinyRoiManager delivering Roi and TextRoi objects.

Author: Bart V. + Elisa
Date: 2025-06-13
Version: 2.2 (scaling + zoom support)
"""

from javax.swing import JFrame, JPanel, WindowConstants, KeyStroke, AbstractAction
from java.awt import Color, Graphics, Graphics2D, RenderingHints, BasicStroke, event
from java.awt.geom.Path2D import Float as java_float
from java.awt.geom import AffineTransform
from java.awt.event import WindowAdapter
from java.awt import Dimension
from java.awt.image import BufferedImage
from ij.process import ColorProcessor
from ij import IJ

# Import TinyRoiManager and all existing Roi/TextRoi objects
from TinyRoiManager import TinyRoiManager
from ij.gui import TextRoi

class RoiImagePanel(JPanel):
    def __init__(self, roi_image):
        JPanel.__init__(self)
        self.roi_image = roi_image
        self.zoom_factor = 1.0

        self.register_zoom_keys()

    def register_zoom_keys(self):
        imap = self.getInputMap(JPanel.WHEN_IN_FOCUSED_WINDOW)
        amap = self.getActionMap()

        imap.put(KeyStroke.getKeyStroke("control EQUALS"), "zoom_in")
        imap.put(KeyStroke.getKeyStroke("control ADD"), "zoom_in")
        imap.put(KeyStroke.getKeyStroke("control MINUS"), "zoom_out")
        imap.put(KeyStroke.getKeyStroke("control SUBTRACT"), "zoom_out")
        imap.put(KeyStroke.getKeyStroke("control 0"), "zoom_reset")

        class ZoomInAction(AbstractAction):
            def actionPerformed(inner_self, e):
                self.zoom_factor *= 1.1
                self.repaint()

        class ZoomOutAction(AbstractAction):
            def actionPerformed(inner_self, e):
                self.zoom_factor /= 1.1
                self.repaint()

        class ZoomResetAction(AbstractAction):
            def actionPerformed(inner_self, e):
                self.zoom_factor = 1.0
                self.repaint()

        amap.put("zoom_in", ZoomInAction())
        amap.put("zoom_out", ZoomOutAction())
        amap.put("zoom_reset", ZoomResetAction())

    def paintComponent(self, g):
        super(RoiImagePanel, self).paintComponent(g)
        g2 = g.create()
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)

        buffered = self.roi_image.getBufferedImage()
        panel_width = self.getWidth()
        panel_height = self.getHeight()

        img_width = buffered.getWidth()
        img_height = buffered.getHeight()

        scale_x = float(panel_width) / img_width
        scale_y = float(panel_height) / img_height
        base_scale = min(scale_x, scale_y)
        total_scale = base_scale * self.zoom_factor

        new_w = int(img_width * total_scale)
        new_h = int(img_height * total_scale)
        x_offset = (panel_width - new_w) // 2
        y_offset = (panel_height - new_h) // 2

        g2.drawImage(buffered, x_offset, y_offset, x_offset + new_w, y_offset + new_h, 0, 0, img_width, img_height, self)

        transform = AffineTransform()
        transform.translate(x_offset, y_offset)
        transform.scale(total_scale, total_scale)
        g2.transform(transform)

        self.roi_image.drawOverlay(g2)
        g2.dispose()

    def panelToImageCoordinates(self, px, py):
        buffered = self.roi_image.getBufferedImage()
        panel_width = self.getWidth()
        panel_height = self.getHeight()

        img_width = buffered.getWidth()
        img_height = buffered.getHeight()

        scale_x = float(panel_width) / img_width
        scale_y = float(panel_height) / img_height
        base_scale = min(scale_x, scale_y)
        total_scale = base_scale * self.zoom_factor

        new_w = int(img_width * total_scale)
        new_h = int(img_height * total_scale)
        x_offset = (panel_width - new_w) // 2
        y_offset = (panel_height - new_h) // 2

        # Terugtransformeren
        ix = (px - x_offset) / total_scale
        iy = (py - y_offset) / total_scale

        return int(ix), int(iy)    


class RoiImage:
    """
    Swing-based ROI image manager fully independent of Fiji windowing.
    Now with automatic scaling and zoom support.
    """

    def __init__(self, image_or_processor, trm=None, on_window_closing=None):
        if hasattr(image_or_processor, 'getProcessor'):
            self.imageplus = image_or_processor
            self.processor = image_or_processor.getProcessor()
        else:
            self.imageplus = None
            self.processor = image_or_processor

        if trm is None:
            raise ValueError("TinyRoiManager (trm) is required.")
        self.trm = trm

        try:
            self.state_style_map = {
                TinyRoiManager.ROI_STATE_ACTIVE: (Color.YELLOW, 1.0),
                TinyRoiManager.ROI_STATE_DELETED: (Color.RED, 1.0),
                TinyRoiManager.ROI_STATE_SELECTED: (Color.BLUE, 5.0)
            }
        except:
            self.state_style_map = {}

        self.use_state_map = True
        self.on_window_closing = on_window_closing
        self.visible = True

        self.frame = JFrame("RoiImage Viewer")
        self.panel = RoiImagePanel(self)
        self.frame.getContentPane().add(self.panel)
        self.frame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)

        if self.on_window_closing is not None:
            class Listener(WindowAdapter):
                def windowClosing(inner_self, event):
                    self.on_window_closing()
            self.frame.addWindowListener(Listener())

        self.panel.setPreferredSize(Dimension(self.processor.getWidth(), self.processor.getHeight()))
        self.frame.pack()

    def getFrame(self):
        return self.frame

    def getBufferedImage(self):
        return self.processor.getBufferedImage()

    def drawOverlay(self, g2d):
        state_order = [
            TinyRoiManager.ROI_STATE_DELETED,
            TinyRoiManager.ROI_STATE_ACTIVE,
            TinyRoiManager.ROI_STATE_SELECTED
        ]

        for target_state in state_order:
            for name, roi, state, tags in self.trm.iter_all():
                if state != target_state:
                    continue
                if state == TinyRoiManager.ROI_STATE_DELETED and not self.show_deleted:
                    continue

                color, stroke = self._get_style_for_state(state)
                g2d.setColor(color)
                g2d.setStroke(BasicStroke(stroke))

                polygon = roi.getPolygon()
                xpoints = polygon.xpoints
                ypoints = polygon.ypoints
                n = polygon.npoints

                path = java_float()
                path.moveTo(xpoints[0], ypoints[0])
                for i in range(1, n):
                    path.lineTo(xpoints[i], ypoints[i])
                path.closePath()
                g2d.draw(path)

                if self.show_labels:
                    label = self.trm.label_array[self.trm.name_to_index[name]]
                    font = label.getCurrentFont()
                    g2d.setFont(font)
                    g2d.setColor(color)
                    g2d.drawString(label.getText(), label.getXBase(), label.getYBase())

    def _get_style_for_state(self, state):
        if self.use_state_map and state in self.state_style_map:
            return self.state_style_map[state]
        elif TinyRoiManager.ROI_STATE_ACTIVE in self.state_style_map:
            return self.state_style_map[TinyRoiManager.ROI_STATE_ACTIVE]
        else:
            return (Color.magenta, 1.0)

    def set_state_map(self, state_map):
        self.state_style_map = dict(state_map)

    def enable_state_map(self, flag):
        self.use_state_map = bool(flag)

    def show(self, overlay=True, show_labels=True, show_deleted=False):
        self.show_labels = show_labels
        self.show_deleted = show_deleted
        self.overlay_enabled = overlay
        self.panel.repaint()
        self.frame.setVisible(True)

    def setVisible(self, flag):
        self.visible = bool(flag)
        self.frame.setVisible(self.visible)

    def getProcessor(self):
        return self.processor

    def getImage(self):
        return self.imageplus
    
