"""

File dialogs

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.

"""
from java.lang import System
from java.io import File
from java.util.prefs import Preferences
from javax.swing import JFileChooser
from javax.swing.filechooser import FileFilter
import os

class JLabelFileChooser(object):
    def __init__(self):
        """
        JFileChooser that only allows files matching specific suffixes
        (_label.png, _label.tif, _label.jpg, _cp_masks.png).
        """
        # Retrieve user.home from Java system properties
        self.user_home = System.getProperty("user.home")
        
        self.prefs = Preferences.userRoot().node("/Fiji/EditRois")
        last_folder_path = self.prefs.get('FileLocation', self.user_home)

        # Create a JFileChooser and set the initial directory
        self.fc = JFileChooser(File(last_folder_path))
        self.fc.setMultiSelectionEnabled(False)
        self.fc.setAcceptAllFileFilterUsed(False)

        # Define a custom FileFilter class that only allows the intended files
        class LabelFileFilter(FileFilter):
            def accept(self, f):
                if f.isDirectory():
                    return True  # Always show directories
                name = f.getName().lower()
                return (name.endswith("_label.png") or
                        name.endswith("_label.tif") or
                        name.endswith("_label.tiff") or
                        name.endswith("_label.jpg") or
                        name.endswith("_cp_masks.png"))

            def getDescription(self):
                return "Label Files (*_label.png, *_label.tif, *_label.tiff, *_label.jpg, *_cp_masks.png)"

        # Attach the filter to the file chooser
        self.fc.setFileFilter(LabelFileFilter())

    def showDialog(self, hint=None):
        """
        Displays the file chooser. Returns a list of paths (strings)
        for the selected files, or None if nothing is selected.
        """
        if hint is not None and os.path.exists(hint):
            self.fc.setSelectedFile(File(hint))
         
        result = self.fc.showOpenDialog(None)
        if result == JFileChooser.APPROVE_OPTION:
            # Retrieve the selected files
            selected_file = self.fc.getSelectedFile()
            # Save the current directory in the preferences
            # (stored as a path rather than just the folder name)
            current_dir = self.fc.getCurrentDirectory()
            self.prefs.put('FileLocation', current_dir.getAbsolutePath())
            return [selected_file.getAbsolutePath()]
        return None

# Example usage:
# chooser = JLabelFileChooser()
# selected = chooser.showDialog()
# if selected:
#     for path in selected:
#         print("Selected:", path)

class JOriginalFileChooser(object):
    def __init__(self):
        """
        JFileChooser that only allows files with .png, .tif, .jpg, or .png.
        """
        self.user_home = System.getProperty("user.home")
        self.prefs = Preferences.userRoot().node("/Fiji/EditRois")
        last_folder_path = self.prefs.get('FileLocation', self.user_home)

        self.fc = JFileChooser(File(last_folder_path))
        self.fc.setMultiSelectionEnabled(True)   # Allow multiple file selection
        self.fc.setAcceptAllFileFilterUsed(False)

        # Define a custom FileFilter class for the required file extensions
        class OriginalFileFilter(FileFilter):
            def accept(self, f):
                if f.isDirectory():
                    return True  # Always show directories
                name = f.getName().lower()
                return (name.endswith(".png") or
                        name.endswith(".tif") or
                        name.endswith(".jpg") or
                        name.endswith(".tiff"))

            def getDescription(self):
                return "Original Files (*.jpg, *.png, *.tif, *.tiff)"

        # Attach the filter to the file chooser
        self.fc.setFileFilter(OriginalFileFilter())

    def showDialog(self):
        """
        Displays the file chooser. Returns a list of paths (strings)
        for the selected files, or None if nothing is selected.
        """
        result = self.fc.showOpenDialog(None)
        if result == JFileChooser.APPROVE_OPTION:
            selected_files = self.fc.getSelectedFiles()
            # assumption: short name = original, long name = label
            l = len(selected_files)
            if l>1:
                selected_files = selected_files[:2]
                selected_files = sorted(selected_files, key=lambda f: len(f.getName()))
            if l>2:    
                print "Trimming number of selected files to 2"
            current_dir = self.fc.getCurrentDirectory()
            self.prefs.put('FileLocation', current_dir.getAbsolutePath())
            file_names = [f.getAbsolutePath() for f in selected_files]
            return file_names
        return None

class JRoiFileChooser(object):
    def __init__(self):
        """
        JFileChooser that only allows files matching specific suffixes
        (*.zip).
        """
        # Retrieve user.home from Java system properties
        self.user_home = System.getProperty("user.home")
        
        # Retrieve preferences (Fiji/LabelsToRois), with 'FileLocation' being the folder
        self.prefs = Preferences.userRoot().node("/Fiji/EditRois")
        last_folder_path = self.prefs.get('FileLocation', self.user_home)

        # Create a JFileChooser and set the initial directory
        self.fc = JFileChooser(File(last_folder_path))
        self.fc.setMultiSelectionEnabled(False)
        self.fc.setAcceptAllFileFilterUsed(False)

        # Define a custom FileFilter class that only allows the intended files
        class ZipFileFilter(FileFilter):
            def accept(self, f):
                if f.isDirectory():
                    return True  # Always show directories
                name = f.getName().lower()
                return (name.endswith(".zip"))

            def getDescription(self):
                return "ROI Files (*.zip)"

        # Attach the filter to the file chooser
        self.fc.setFileFilter(ZipFileFilter())

    def showDialog(self):
        """
        Displays the file chooser. Returns a list of paths (strings)
        for the selected files, or None if nothing is selected.
        """
         
        result = self.fc.showOpenDialog(None)
        if result == JFileChooser.APPROVE_OPTION:
            # Retrieve the selected files
            selected_file = self.fc.getSelectedFile()
            current_dir = self.fc.getCurrentDirectory()
            self.prefs.put('FileLocation', current_dir.getAbsolutePath())
            ret_value = [selected_file.getAbsolutePath()]
            return ret_value
        return None