"""
DoTheWorkFrame.py

Graphical user interface (GUI) frame for eroding, saving, and selecting ROIs
in the 'Edit ROIs' Fiji plugin. This class manages button callbacks,
checkbox states, and coordinates overlay updates based on user input.

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.

"""

from javax.swing import JFrame, JLabel, JButton, JTextField, JCheckBox, BoxLayout, JOptionPane, JPanel
from javax.swing import WindowConstants
from java.awt.event import WindowAdapter
from java.awt import Font, Color, BorderLayout, Dimension
from java.awt import Toolkit, Window
from java.awt import Rectangle
from ij import IJ
from ij.gui import Roi
from RoiIo import RoiIo

import sys
import os
import time

from TinyRoiManager import TinyRoiManager

def get_timestamp_string():
    """Return current time as a string in yyyymmddHHMMSS format."""
    return time.strftime("%Y%m%d%H%M%S")

class DoTheWorkFrame:
    def __init__(self, gvars):
        self.gvars = gvars
        self.rm = TinyRoiManager.getInstance2()

        self.frame = JFrame("Edit Rois - Do the work!")
        self.frame.setSize(450, 300)
        self.frame.setLayout(None)
        self.frame.setResizable(False)
        self.frame.setLocation(0, 0)
        self.frame.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)
        self.frame.addWindowListener(self.DoTheWorkFrameAdapter(self))

        self.frm_delete = JFrame("DELETE")
        self.frm_delete.setSize(200, 120)
        self.frm_delete.setLayout(BorderLayout())
        self.frm_delete.setAlwaysOnTop(True)
        self.frm_delete.setResizable(False)
        screenSize = Toolkit.getDefaultToolkit().getScreenSize()
        self.frm_delete.setLocation(0, (screenSize.height - self.frm_delete.getHeight()) // 2)
        self.frm_delete.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE)

        self.init_components()

    def init_components(self):

        self.btn_saveRois = JButton("Save ROIs", actionPerformed=self.on_save_rois)
        self.btn_saveRois.setBounds(250, 70, 150, 20)

        self.btn_outliers = JButton("Select Outliers", actionPerformed=self.on_select_outliers)
        self.btn_outliers.setBounds(60, 110, 150, 20)
        self.btn_outliers.setEnabled(True)

        self.btn_saveTable = JButton("Save Measurements", actionPerformed=self.on_save_table)
        self.btn_saveTable.setBounds(250, 110, 150, 20)

        self.btn_outer_vdb = JButton("Select Outer vdb", actionPerformed=self.on_outer_vdb)
        self.btn_outer_vdb.setBounds(60, 150, 150, 20)

        self.btn_outer_ghm = JButton("Select Outer vdb 2", actionPerformed=self.on_outer_vdb_fancy)
        self.btn_outer_ghm.setBounds(250, 150, 150, 20)

        self.btn_prev = JButton("Previous", actionPerformed=self.on_previous)
        self.btn_prev.setBounds(60, 230, 150, 20)

        self.btn_finish = JButton("Finish", actionPerformed=self.on_finish)
        self.btn_finish.setBounds(250, 230, 150, 20)

        self.cb_show_names = JCheckBox("Show names", self.gvars.get("show_names", True), actionPerformed=self.on_toggle_show_names)
        self.cb_show_deleted = JCheckBox("Show deleted", self.gvars.get("show_deleted", True), actionPerformed=self.on_toggle_show_deleted)
        pnl = JPanel()
        pnl.setLayout(BoxLayout(pnl, BoxLayout.Y_AXIS))
        pnl.setBounds((450-100)//2, 180, 100, 50)
        pnl.add(self.cb_show_names)
        pnl.add(self.cb_show_deleted)


        self.frame.add(self.btn_saveRois)
        self.frame.add(self.btn_outliers)
        self.frame.add(self.btn_saveTable)
        self.frame.add(self.btn_outer_vdb)
        self.frame.add(self.btn_outer_ghm)
        self.frame.add(self.btn_prev)
        self.frame.add(self.btn_finish)
        self.frame.add(pnl)

        btn_delete = JButton("DELETE", actionPerformed=self.on_delete_selected)
        btn_delete.setForeground(Color.WHITE)
        btn_delete.setBackground(Color.RED)
        btn_delete.setFont(Font("Dialog", Font.BOLD, 36))
        btn_delete.setPreferredSize(Dimension(150, 70))
        self.frm_delete.add(btn_delete, BorderLayout.CENTER)

    def goto(self,sender=None):
        self.show()
    
    def show(self):
        self.frame.setVisible(True)
        self.frm_delete.setVisible(True)

    def on_save_rois(self, event):
        self.save_rois(as_backup=False)
    
    def save_rois(self,as_backup=False):
        ri=RoiIo.getInstance()
        all_but_ext, _ = os.path.splitext(self.gvars["path_original_image"])
        if as_backup:
            now=get_timestamp_string()
            backup_folder = os.path.dirname(all_but_ext)+"/RoiBackup/"
            filename_wo_ext = os.path.basename(all_but_ext)
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)
                IJ.log("Create backup folder for ROIs: "+backup_folder)
            full_name = backup_folder + now + "_" + filename_wo_ext+"_RoiBackup.zip"
        else:
            full_name = all_but_ext + "_RoiSet.zip"
            ri.save_to_zip(full_name)
        IJ.log("ROIs saved: " + full_name)

    def on_select_outliers(self, event):
        IJ.log("Selecting and tagging Outliers")
        last_selected_msmt = self.gvars["selected_measurement_name"]
        outliers=self.gvars["Measurements"].outliers["ACTIVE"][last_selected_msmt]
        self.rm.select(outliers,reason_of_selection="IQR."+last_selected_msmt,additive=True)
        self.refresh_overlay()

    def on_save_table(self, event):
        self.gvars["Measurements"].save_all(self.gvars['path_original_image'])

    def on_outer_vdb(self, event):
        def compute_step(x):
            fx = max(0.0, min(1.0, (3000.0 - x) / 800.0))
            return int(fx * 9.0 + 1.0)
        imp=self.gvars["working_image"].getImage()
        w = imp.getWidth()
        h = imp.getHeight()
        step = compute_step(max(w,h))
        from RoiSelect import select_outer_rois_vdb
        IJ.log("Starting scan of outer edge using vdb's algorithm using step (degrees): " + str(step))
        select_outer_rois_vdb(step)
        self.refresh_overlay()

    def on_outer_vdb_fancy(self, event):
        from RoiSelect import select_outer_rois_vdb_fancy
        def compute_step(x):
            fx = max(0.0, min(1.0, (2700.0 - x) / 800.0))
            return int(fx * 9.0 + 1.0)
        imp=self.gvars["working_image"].getImage()
        w = imp.getWidth()
        h = imp.getHeight()
        step = compute_step(max(w,h))
        select_outer_rois_vdb_fancy(step)
        self.refresh_overlay()

    def on_previous(self, event):
        self.save_rois(as_backup=True)
        self.setVisible(False)
        self.gvars['EditRoisStartUpFrame'].goto(self)

    def on_finish(self, event):
        self.setVisible(False)
        IJ.log("Finishing plugin")
        self.save_rois(as_backup=True)
        for w in Window.getWindows():
            if hasattr(w, "getTitle") and w.getTitle() not in {"Log", "Console", "(Fiji Is Just) ImageJ"}:
                w.dispose()
        print("Doei doei, lieve Kaat")
        sys.exit(0)

    def on_toggle_show_names(self, event):
        self.gvars["show_names"] = self.cb_show_names.isSelected()
        self.refresh_overlay()

    def on_toggle_show_deleted(self, event):
        self.gvars["show_deleted"] = self.cb_show_deleted.isSelected()
        self.refresh_overlay()

    def refresh_overlay(self):
        roi_image = self.gvars.get("working_image")
        if roi_image:
            roi_image.show(overlay=True, show_labels=self.gvars["show_names"], show_deleted=self.gvars["show_deleted"])

    def on_delete_selected(self, event):
        self.rm.delete_selected()
        self.gvars["Measurements"].data_have_changed("delete_selected")
        self.refresh_overlay()
        
    def on_delete_key_pressed(self,argument):
        IJ.log("DELETE key pressed")
        self.rm.delete_selected()
        self.gvars["Measurements"].data_have_changed("delete_key")
        self.refresh_overlay()   

    def on_escape_key_pressed(self,argument):
        IJ.log("ESCAPE key pressed")
        self.rm.unselect_all()
        self.refresh_overlay()
        
    def on_f1_key_pressed(self,argument):
        IJ.log("F1 key pressed")

        # roi_image = self.gvars.get("working_image").getImage()
        # roi = roi_image.getRoi()
        # if roi is None:
        #     IJ.log("F1 pressed but no rectangle indicated on screen")
        #     return
        # if not isinstance(roi, Roi) or roi.getType()!=Roi.RECTANGLE:
        #     return
        # rect = roi.getBounds()
        # self.rm.select_within(rect,additive=True)
        # self.refresh_overlay()
        # roi_image.deleteRoi()

    def  on_rectangle_select(self, rect):
        IJ.log("rectangle select")
        self.rm.select_within(rect,additive=True)
        self.refresh_overlay()


    def on_tagged_delete(self,tag):
        IJ.log("Function key pressed for tagged delete: "+tag)
        self.rm.delete_selected(tag)
        self.gvars["Measurements"].data_have_changed("delete_key")
        #self.gvars["Measurements"].RecalculateWorker.execute()
        self.refresh_overlay()   
    
        
        
    def setVisible(self, flag):
        """Set visibility of main and delete frame."""
        self.frame.setVisible(flag)
        self.frm_delete.setVisible(flag)

    class DoTheWorkFrameAdapter(WindowAdapter):
        def __init__(self, outer):
            self.outer = outer
        def windowClosing(self, event):
            self.outer.on_previous(event)
