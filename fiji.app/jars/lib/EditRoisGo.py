"""
EditRoisGo.py

Entry point for the 'Edit ROIs' Fiji plugin.
Initializes global variables, prepares UI layout and logging, sets preferences,
instantiates main classes, and sets up key interception.

Author: Bart V. + Elisa
Date: 2025-03-30
"""

import os
import sys
import datetime
from tempfile import NamedTemporaryFile

from java.awt import Toolkit, Window
from java.util.prefs import Preferences
from java.lang import System

from ij import IJ, Prefs, WindowManager

from Tee import Tee
from EditRoisStartUpFrame import EditRoisStartUpFrame
from DoTheWorkFrame import DoTheWorkFrame
from TinyRoiManager import TinyRoiManager as RoiManager
from RoiIo import RoiIo
from RoiImage import RoiImage

"""
only the function keys can be assigned
F1 is already in use (click-hold-drag-select), F1 selects and does not delete
a label can be attached to F2 ... F12
the function of function keys is 'for all selected: tag with label and delete' 
"""
key_to_label_map = { "F5" : "freeze",           # all but the last line must end with comma
                     "F6" : "fold",
                     "F7" : "vessel",
                     "F9" : "section.tear",
                     "F10" : "section.stretch"   # last line must not end with comma  

}

def just_go_for_it():
    gvars = {}

    # Core configuration
    gvars["pixels_per_logical_processor"] = 500000
    gvars["max_number_of_rois"] = 4095
    gvars["load_zip_batch_size"] = 384

    rm = RoiManager(gvars)
    ri = RoiIo(gvars)

    screen_size = Toolkit.getDefaultToolkit().getScreenSize()



    # Position JVM console window
    for w in Window.getWindows():
        if hasattr(w, "getTitle") and (w.getTitle() == "Console" or w.getTitle() == "Edit"):
            w.setLocation(0, screen_size.height - w.getSize().height - 100)
            w.setVisible(True)
            break

    print "Hallo Kaat!"

    ij_instance = IJ.getInstance()

    if ij_instance is not None:
        # Configure ImageJ's monospaced text rendering
        IJ.runMacro('setOption("MonospacedText", true);')
        IJ.log("Edit ROIs - plugin started inside Fiji")
        log_win = WindowManager.getWindow("Log")
        log_win.setVisible(False)
        log_win.setSize(screen_size.width // 5, log_win.getSize().height)
        log_win.setLocation(screen_size.width - log_win.getSize().width,
                             screen_size.height - log_win.getSize().height - 100)
        log_win.setVisible(True)        
    else:
        print("Running standalone without starting Fiji")



    # Default session settings
    gvars['eroded_pixels'] = 0
    gvars['show_names'] = True
    gvars['show_deleted'] = True

    # Prepare temporary ROI file
    temp_file = NamedTemporaryFile(suffix='.zip')
    gvars['tempFile'] = temp_file.name

    Prefs.useNamesAsLabels = True

    # Prepare logging
    user_home = System.getProperty("user.home")
    log_folder = os.path.join(user_home, "FijiLog")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    datetime_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    console_filename = os.path.join(log_folder, datetime_str + "_Fiji_console_output.txt")
    IJ.log("Edit ROIs - Logfile: " + console_filename)
    sys.stdout = Tee(console_filename)

    # Center main ImageJ window
    for w in Window.getWindows():
        if hasattr(w, "getTitle") and w.getTitle() == "(Fiji Is Just) ImageJ":
            w.setLocation((screen_size.width - w.getSize().width) // 2, 0)
            w.setResizable(False)
            break

    # Store last-used file location
    prefs = Preferences.userRoot().node("/Fiji/EditRois")
    prefs.put("FileLocation", prefs.get("FileLocation", user_home))

    # Set measurements
    msmt = "area feret's area_fraction display redirect=None decimal=3"
    IJ.run("Set Measurements...", msmt)
    print "Edit ROIs - Set measurements: " + msmt

    # Show the startup frames
    frame3 = DoTheWorkFrame(gvars)
    gvars['DoTheWorkFrame'] = frame3
    frame2 = EditRoisStartUpFrame(gvars)
    gvars['EditRoisStartUpFrame'] = frame2

    # Set up keyboard interception
    from java.awt.event import KeyEvent
    from RoyalKeyInterceptor import RoyalKeyInterceptor
    
    name_to_code = {    "F2" : KeyEvent.VK_F2,
                        "F3" : KeyEvent.VK_F3,
                        "F4" : KeyEvent.VK_F4,
                        "F5" : KeyEvent.VK_F5,
                        "F6" : KeyEvent.VK_F6,
                        "F7" : KeyEvent.VK_F7,
                        "F8" : KeyEvent.VK_F8,
                        "F9" : KeyEvent.VK_F9,
                        "F10": KeyEvent.VK_F10,
                        "F11": KeyEvent.VK_F11,
                        "F12": KeyEvent.VK_F12                        
    }
    
    interceptor_key_action = {      KeyEvent.VK_ESCAPE: (gvars['DoTheWorkFrame'].on_escape_key_pressed,None, True),
                                    KeyEvent.VK_DELETE: (gvars['DoTheWorkFrame'].on_delete_key_pressed,None, True),
                                    KeyEvent.VK_F1: (gvars['DoTheWorkFrame'].on_f1_key_pressed,None, True)
    }
                            
    for name,label in key_to_label_map.items():
        interceptor_key_action[name_to_code[name]] = (gvars['DoTheWorkFrame'].on_tagged_delete,label,True)

    interceptor = RoyalKeyInterceptor(gvars, interceptor_key_action)
    interceptor.install()
    
    print "User defined key mapping for tagged delete:"
    for name,label in key_to_label_map.items():
        print name+ " -> "+label
    
    IJ.log("Edit ROIs - end of startup script")
