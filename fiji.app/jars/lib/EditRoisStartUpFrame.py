from javax.swing import JFrame, JPanel, JLabel, JButton, JTextField, JCheckBox, BoxLayout, JOptionPane
from java.awt import Toolkit, Color
from java.awt.event import WindowAdapter
from java.awt import Window

from javax.swing import WindowConstants
from java.awt import Dimension, Font, BorderLayout
 
from ij import IJ
#from ij.plugin.frame import RoiManager
from FileChoosers import JOriginalFileChooser, JLabelFileChooser, JRoiFileChooser
from java.lang import System

from RoiMeasurements import RoiMeasurements,ComputeAllWorker
from LabelToRoiTask import LabelToRoiTask
from MouseListener import ROIClickListener

from TinyRoiManager import TinyRoiManager as RoiManager
from RoiImage import RoiImage
from RoiIo import RoiIo

def clean_up():
    IJ.log("Edit ROIs - closing plug in")
    for w in Window.getWindows():
        if hasattr(w, "getTitle") and not (w.getTitle() in {"Log", "(Fiji Is Just) ImageJ", "Console"}):
            w.dispose()
    IJ.log("Edit ROIs - all cleaned up")
    print "Doei, doei, lieve Kaat"

class Frame2WindowAdapter(WindowAdapter):
    def windowClosing(self, event):
        clean_up()

def on_image_window_closing():
    clean_up()

# JFrame-derived class
class EditRoisStartUpFrame(JFrame):

    def __init__(self,gvars):
    
        JFrame.__init__(self, "Edit ROIs - Choose paths")
        self.gvars=gvars
        self.hint=None
        
        self.setSize(450, 350)
        self.setLocation(0, 100)
        self.setLayout(None)
        self.setResizable(False)
        self.addWindowListener(Frame2WindowAdapter())
        self.glassPane = self.getGlassPane()
        self.glassPane.setVisible(False)
        
        # Original image components
        lbl_original = JLabel("Path to original image")
        lbl_original.setBounds(30, 20, 200, 20)
        self.add(lbl_original)
        
        self.btn_original = JButton("Browse", actionPerformed=self.on_click_browse_original)
        self.btn_original.setBounds(170, 20, 100, 20)
        self.add(self.btn_original)
        
        self.txt_original = JTextField(10)
        self.txt_original.setBounds(280, 20, 120, 20)
        self.add(self.txt_original)
        
        # Label image components
        lbl_label = JLabel("Path to label image")
        lbl_label.setBounds(30, 50, 200, 20)
        self.add(lbl_label)
        
        self.btn_label = JButton("Browse", actionPerformed=self.on_click_browse_label)
        self.btn_label.setBounds(170, 50, 100, 20)
        self.add(self.btn_label)
        
        self.txt_label = JTextField(10)
        self.txt_label.setBounds(280, 50, 120, 20)
        self.add(self.txt_label)
        
        # Zip/ROI file components
        lbl_zip = JLabel("Path to zip/roi file")
        lbl_zip.setBounds(30, 80, 200, 20)
        self.add(lbl_zip)
        
        self.btn_zip = JButton("Browse", actionPerformed=self.on_click_browse_zip)
        self.btn_zip.setBounds(170, 80, 100, 20)
        self.add(self.btn_zip)
        
        self.txt_zip = JTextField(10)
        self.txt_zip.setBounds(280, 80, 120, 20)
        self.add(self.txt_zip)
        
        # Panel with checkboxes and textfield for size threshold
        pnl = JPanel()
        pnl.setLayout(BoxLayout(pnl, BoxLayout.Y_AXIS))
        pnl.setBounds(120, 120, 200, 100)
        self.cbEdge = JCheckBox("Remove at edge", True)
        self.cbSmall = JCheckBox("Remove small", True)
        self.cbPixel = JCheckBox("Force pixel as unit", True)
        self.tbSize = JTextField(10)
        self.tbSize.setText("100")
        pnl.add(self.cbEdge)
        pnl.add(self.cbSmall)
        pnl.add(self.cbPixel)
        pnl.add(self.tbSize)
        self.add(pnl)
        
        # Next button
        self.btn_next = JButton("Next", actionPerformed=self.on_click_browse_next)
        self.btn_next.setBounds(300, 250, 100, 20)
        self.add(self.btn_next)
        
        self.setVisible(True)
        
    def goto(self,sender=None):
        IJ.log("Edit ROIs - cleaning up while returning to start up frame")
        self.gvars["eroded_pixels"] = 0
        if "working_image" in self.gvars:
            self.gvars["working_image"].getImage().close()
        for key in ['path_original_image', 'path_zip_file', 'path_label_image','working_image']:
            self.gvars.pop(key, None)
        self.txt_original.setText("")
        self.txt_zip.setText("")
        self.txt_label.setText("")
        #rm=RoiManager.getInstance2()
        #rm.reset()
        for w in Window.getWindows():
            if w is not self and hasattr(w, "getTitle") and w.getTitle() not in {"Log", "Console", "(Fiji Is Just) ImageJ"}:
                w.dispose()
        self.setVisible(True)

    
    def on_click_browse_original(self, event):
        fc = JOriginalFileChooser()
        result = fc.showDialog()
        if result is not None:
            if len(result) == 2:
                self.hint = result[1]
                IJ.log("Hint for label image: " + self.hint)
                self.gvars['path_label_image'] = self.hint
                self.txt_label.setText(str(self.gvars['path_label_image']))
            else:
                self.hint = None
            message = 'Path to original image %s' % result[0]
            print message
            self.gvars['path_original_image'] = result[0]
            self.txt_original.setText(self.gvars['path_original_image'])
        else:
            message = 'Original: Request canceled by user'
        IJ.log(message)
    
    def on_click_browse_label(self, event):
        fc = JLabelFileChooser()
        result = fc.showDialog(self.hint)
        self.hint = None
        if result is not None:
            message = 'Path to label image %s' % result[0]
            self.gvars['path_label_image'] = result[0]
            self.txt_label.setText(str(self.gvars['path_label_image']))
        else:
            message = 'Label image: Request canceled by user'
        IJ.log(message)
    
    def on_click_browse_zip(self, event):
        fc = JRoiFileChooser()
        result = fc.showDialog()
        if result is not None:
            message = 'Path to zip/roi file %s' % result[0]
            self.gvars['path_zip_file'] = result[0]
            self.txt_zip.setText(str(self.gvars['path_zip_file']))
        else:
            message = 'Zip: Request canceled by user'
        IJ.log(message)
    

    def on_click_browse_next(self, event):

        if 'path_label_image' not in self.gvars.keys():
            JOptionPane.showMessageDialog(None, "You have to choose at least a label image")
            return
        
        if 'path_original_image' not in self.gvars.keys():
            self.gvars['path_original_image'] = self.gvars['path_label_image']
            System.err.println("Edit ROIs - No original image, using label image as background")
        
        try:
            size_threshold = int(self.tbSize.getText())
            if size_threshold < 0:
                size_threshold = abs(size_threshold)
                System.err.println("Negative size threshold value entered, absolute value used: " + str(size_threshold))
                self.tbSize.setText(str(size_threshold))
        except:
            size_threshold = 100
            System.err.println("Invalid size threshold value entered, restored default: " + str(size_threshold))

        ## open the background image
        imp_background = IJ.openImage(self.gvars['path_original_image'])
        if not imp_background:
            System.err.println("Could not open background image: " + self.gvars['path_original_image'])
            IJ.beep()
            IJ.beep()
            IJ.beep()
            self.goto(self)
            return
        
        ## open the label image
        imp_lbl = IJ.openImage(self.gvars['path_label_image'])
        if not imp_lbl:
            System.err.println("Could not open label image: " + self.gvars['path_label_image'])
            IJ.beep()
            IJ.beep()
            IJ.beep()
            self.goto(self)
            return

        background_width = imp_background.getWidth()
        background_height = imp_background.getHeight()
        label_width = imp_lbl.getWidth()
        label_height = imp_lbl.getHeight()
        if background_width != label_width or background_height != label_height:
            System.err.println("Image dimensions of the selected images do not match")
            System.err.println("Background image: " + self.gvars['path_original_image'])
            System.err.println("does not match")
            System.err.println("Label image     : " + self.gvars['path_label_image'])
            IJ.beep()
            IJ.beep()
            IJ.beep()
            self.goto(self)
            return

        
        self.glassPane.setVisible(True)
        
        self.tbSize.setText(str(size_threshold))
        self.gvars['size_threshold'] = size_threshold
        self.gvars['remove_edges'] = self.cbEdge.isSelected()
        self.gvars['remove_small'] = self.cbSmall.isSelected()
        self.gvars['force_pixel'] = self.cbPixel.isSelected()
        print "Remove at edges: " + str(self.gvars['remove_edges']) + " | Force pixel as unit: " + str(self.gvars['force_pixel']) + " | Remove small: " + str(self.gvars['remove_small']) + " | size threshold: " + str(self.gvars['size_threshold'])
        
        roi_image= RoiImage(imp_background,RoiManager.getInstance2(),on_window_closing=on_image_window_closing,on_rectangle_select=self.gvars['DoTheWorkFrame'].on_rectangle_select)
        self.gvars["working_image"] = roi_image
        roi_image.show(overlay=True,show_labels=self.gvars["show_names"],show_deleted=self.gvars["show_deleted"])
        
        imp_frame = roi_image.frame
        imp_frame.setResizable(True)
        imp_frame_size = imp_frame.getSize()
        screenSize = Toolkit.getDefaultToolkit().getScreenSize()
        imp_frame.setLocation((screenSize.width - imp_frame_size.width) // 2,
                              (screenSize.height - imp_frame_size.height) // 2)
        
        cal = imp_background.getCalibration()
        message = "CALIBRATION read from image: Unit: " + cal.getUnit() + " | Pixel Width: " + str(cal.pixelWidth) + " | Pixel Height: " + str(cal.pixelHeight) + " | Pixel Depth: " + str(cal.pixelDepth)
        System.err.println(message)
        
        if self.gvars['force_pixel']:
            cal.setUnit("pixel")
            cal.pixelWidth = 1.0
            cal.pixelHeight = 1.0
            cal.pixelDepth = 1.0
            imp_background.setCalibration(cal)
            cal = imp_background.getCalibration()
            message = "CALIBRATION forced to     : Unit: " + cal.getUnit() + " | Pixel Width: " + str(cal.pixelWidth) + " | Pixel Height: " + str(cal.pixelHeight) + " | Pixel Depth: " + str(cal.pixelDepth)
            System.err.println(message)
            IJ.log(message)
            IJ.beep()
        
        from ij.plugin import ContrastEnhancer
        ce = ContrastEnhancer()
        percent_as_fraction = 35.0/100.0
        ce.stretchHistogram(imp_background, percent_as_fraction)
        
        self.gvars['label_image'] = imp_lbl
        

        
        if 'path_zip_file' not in self.gvars.keys():
            IJ.log("No zip/roi file selected, creating ROIs from labels")
            task = LabelToRoiTask(imp_lbl, self.gvars,self.continuation_after_loading)
            task.start()
        else:
            IJ.log("Zip file selected, reading ROIs from file: " + self.gvars["path_zip_file"])
            rm = RoiManager.getInstance2()
            ri=RoiIo.getInstance()
            rm.reset
            ri.load_from_zip(self.gvars["path_zip_file"],imp_lbl)
            self.continuation_after_loading()

       
    def continuation_after_loading(self):

        rm = RoiManager.getInstance2()
        roi_image=self.gvars["working_image"]

        roi_image.show(overlay=True,show_labels=self.gvars["show_names"],show_deleted=self.gvars["show_deleted"])
        imp_lbl=self.gvars['label_image']

        listener = ROIClickListener(roi_image, imp_lbl,self.gvars)
        listener.activate()

        msmts = RoiMeasurements(self.gvars)

        worker = ComputeAllWorker(msmts,self.gvars, self.continuation_after_crunching)

        worker.execute()

        
    def continuation_after_crunching(self):
        self.setVisible(False)
        self.glassPane.setVisible(False)
        nextFrame = self.gvars['DoTheWorkFrame']    
        nextFrame.goto(self)
        

