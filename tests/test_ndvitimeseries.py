# -*- coding: utf-8 -*-
"""
test_roitimeseries
------------------

Tests for `vegindex.ndvitimeseries` module.
"""

import os

import numpy as np
from PIL import Image
from pkg_resources import Requirement
from pkg_resources import resource_filename

from vegindex import config
from vegindex import ndvitimeseries

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

config.archive_dir = SAMPLE_DATA_DIR


def test_reading_ndvits_file():
    """
    test reading in existing ndvits timeseries
    """

    sitename = "dukehw"
    roiname = "DB_1000"
    ndvi_file = "{}_{}_NDVI_roistats.csv".format(sitename, roiname)

    # set up path to roistats file
    ndvi_path = os.path.join(SAMPLE_DATA_DIR, sitename, "ROI", ndvi_file)

    ndvits = ndvitimeseries.NDVITimeSeries(site=sitename, ROIListID=roiname)

    ndvits.readCSV(ndvi_path)
    first_row = ndvits.rows[0]
    last_row = ndvits.rows[-1]

    np.testing.assert_equal(last_row["filename_rgb"], "dukehw_2020_07_15_215405.jpg")
    np.testing.assert_equal(last_row["filename_ir"], "dukehw_IR_2020_07_15_215405.jpg")
    np.testing.assert_equal(first_row["exposure_rgb"], 34)
    np.testing.assert_equal(first_row["exposure_ir"], 8)
    np.testing.assert_equal(len(ndvits.rows), 93946)
