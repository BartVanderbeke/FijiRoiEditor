"""

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
"""
from ij import IJ
#from ij.plugin.frame import RoiManager
from ij.gui import Roi as ROI
import math
from TinyRoiManager import TinyRoiManager as RoiManager

def select_outer_rois_graham():
    """
    selects the ROIs from the ROI Manager that form the outer layer,
    using the Graham scan algorithm
    i.e., those determined as the vertices of the convex hull of all ROI centroids.
    """
    rm = RoiManager.getInstance2()
    if not rm:
        IJ.Log("select_outer_rois_graham: No ROI Manager")
        return

    n = len(rm)   #.getCount()
    if n == 0:
        IJ.Log("select_outer_rois_graham: No ROIs in ROI Manager")
        return  # No ROIs to process
    
    # Check the first ROI for the attribute
    first_roi = rm.get_sample()
    use_contour = hasattr(first_roi, 'getContourCentroid')
    
    # Collect the centroid for each ROI using two separate loops based on the check
    roi_centroids = []
    if use_contour:
        #for i in range(n):
        for (_, roi, _, _) in rm:
            #roi = rm.getRoi(i)
            centroid = roi.getContourCentroid()  # Expected to return an object with attributes x and y
            cx, cy = centroid[0], centroid[1]
            roi_centroids.append((cx, cy, roi))
    else:
        #for i in range(n):
        for (_, roi, _, _) in rm:
            #roi = rm.getRoi(i)
            bounds = roi.getBounds()
            cx = bounds.x + bounds.width / 2.0
            cy = bounds.y + bounds.height / 2.0
            roi_centroids.append((cx, cy, roi))
    
    # Helper function: compute the convex hull using the Graham scan algorithm
    def convex_hull(points):
        # Sort the points by x, then by y
        points = sorted(points, key=lambda p: (p[0], p[1]))
        
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        
        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        
        # Combine lower and upper to form the convex hull (avoiding duplicates)
        hull = lower[:-1] + upper[:-1]
        return hull

    # Compute the convex hull of the ROI centroids
    hull = convex_hull(roi_centroids)
    hull_indices = set([p[2] for p in hull])
    # Collect the indices into a list and select them all at once
    to_be_selected_rois = sorted(list(hull_indices))
    #print "ROIs at outer edge: ",hull_indices
    #rm.setSelectedIndexes(selected_indices)
    rm.select(to_be_selected_rois, additive=True)
    print "ROIs at outer edge selected using Graham's algorithm"
    

   
def select_outer_rois_vdb(step=10):

    rm = RoiManager.getInstance2()
    if not rm:
        IJ.Log("select_outer_rois_vdb: No ROI Manager")
        return

    n = len(rm)   #.getCount()
    if n == 0:
        IJ.Log("select_outer_rois_vdb: No ROIs in ROI Manager")
        return  # No ROIs to process

    # Compute centers of all ROIs
    def roi_center(roi):
        stats = roi.getStatistics()
        return stats.xCentroid, stats.yCentroid, roi

    roi_centers = rm.map_over_rois(roi_center)

    # Compute the simple average position (center of centers)
    num_rois = len(roi_centers)
    x_avg = sum(c[0] for c in roi_centers) // num_rois
    y_avg = sum(c[1] for c in roi_centers) // num_rois

    # Identify furthest ROI per angular bin directly
    num_bins = 360 // step
    furthest_in_bin = [(-1, None)] * num_bins

    for x, y, roi in roi_centers:
        dx = x - x_avg
        dy = y - y_avg
        r = math.hypot(dx, dy)
        theta_deg = int(math.degrees(math.atan2(dy, dx))) % 360
        theta_bin_deg = (theta_deg // step) % num_bins

        if r > furthest_in_bin[theta_bin_deg][0]:
            furthest_in_bin[theta_bin_deg] = (r, roi)

    # Collect indices of outer ROIs

    to_be_selected_rois = {roi for r, roi in furthest_in_bin if roi is not None}
    rm.select(to_be_selected_rois,reason_of_selection="edge.section", additive=True)
    #print "ROIs at outer edge selected using vdb's algorithm"


def select_outer_rois_vdb_fancy(step=10):
    rm = RoiManager.getInstance2()
    if not rm:
        IJ.Log("select_outer_rois_vdb_fancy: No ROI Manager")
        return

    n = len(rm)
    if n == 0:
        IJ.Log("select_outer_rois_vdb_fancy: No ROIs in ROI Manager")
        return

    # Bereken bounding box-hoeken per ROI
    def roi_farthest_bbox_point(roi):
        bounds = roi.getBounds()
        corners = [
            (bounds.x, bounds.y),
            (bounds.x + bounds.width, bounds.y),
            (bounds.x, bounds.y + bounds.height),
            (bounds.x + bounds.width, bounds.y + bounds.height),
        ]
        return corners, roi

    roi_boxes = rm.map_over_rois(roi_farthest_bbox_point)

    # Bereken gemiddelde van alle ROI-centra (midden van bounding boxes)
    x_avg = sum((sum(x for x, y in corners) / 4.0) for corners, roi in roi_boxes) // n
    y_avg = sum((sum(y for x, y in corners) / 4.0) for corners, roi in roi_boxes) // n

    # Kies per ROI het verste hoekpunt t.o.v. (x_avg, y_avg)
    def farthest_corner(corners, roi):
        return max(corners, key=lambda pt: (pt[0] - x_avg) ** 2 + (pt[1] - y_avg) ** 2), roi

    roi_farthest_points = [farthest_corner(corners, roi) for corners, roi in roi_boxes]

    # Verdeel in hoeken en kies per sector de verste
    num_bins = 360 // step
    furthest_in_bin = [(-1, None)] * num_bins

    for (x, y), roi in roi_farthest_points:
        dx = x - x_avg
        dy = y - y_avg
        r = math.hypot(dx, dy)
        theta_deg = int(math.degrees(math.atan2(dy, dx))) % 360
        theta_bin = (theta_deg // step) % num_bins

        if r > furthest_in_bin[theta_bin][0]:
            furthest_in_bin[theta_bin] = (r, roi)

    # Selecteer de verste ROIs
    to_be_selected_rois = {roi for r, roi in furthest_in_bin if roi is not None}
    rm.select(to_be_selected_rois,reason_of_selection="edge.section", additive=True)
    #print "ROIs at outer edge selected using fancy bounding box method"


