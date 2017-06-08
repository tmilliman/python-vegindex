# -*- coding: utf-8 -*-

import sys

import numpy as np
from PIL import Image


class ROIMask(object):
    """
    Class for ROI Mask File
    """

    def __init__(self, ROIList_id, start_dt, end_dt, maskfile, sample_image):
        """
        Create ROIMask object - right now there is no database entry for
        an individual mask file but we might add one at some point.  That
        way we could have a form for creating a ROIList complete with
        a list of masks.  Right now we just create an dummy entry.

        At some point we also might want to add a comment field so we
        know why the new mask was added ... initial mask, FOV shift,
        avoid new ref. panel, etc
        """

        self.ROIList_id = ROIList_id
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.maskfile = maskfile
        self.sample_image = sample_image

        # get sitename, roi-type, sequence number from ID
        [s1, s2, s3] = self.ROIList_id.split('_')
        self.site = s1
        self.roitype = s2
        self.sequence_number = int(s3)

    def formatCSVRow(self):
        """
        Return a string which can be used as a row in an
        ROIList CSV file.
        """

        # CSV has start_date, start_time, end_date, end_time,
        # maskfile, sample_image
        start_date = self.start_dt.date()
        start_time = self.start_dt.time()
        end_date = self.end_dt.date()
        end_time = self.end_dt.time()
        csvrow = '{0},{1},{2},{3},{4},{5}'.format(start_date, start_time,
                                                  end_date, end_time,
                                                  self.maskfile,
                                                  self.sample_image)
        return csvrow

    def read(self, roiMaskPath):
        """
        Read ROIMask file and return a numpy array.
        """

        # read using PIL
        try:
            mask_img = Image.open(roiMaskPath)
        except:
            sys.stderr.write("Unable to open mask file\n")
            return None

        # convert to numpy boolean mask
        mask = np.asarray(mask_img, dtype=np.bool8)

        return mask
