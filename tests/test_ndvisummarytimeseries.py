# -*- coding: utf-8 -*-
"""
test_ndvisummarytimeseries
--------------------------

Tests for `vegindex.ndvi_summary_timeseries` module.
"""

import os

import numpy as np
from PIL import Image
from pkg_resources import Requirement
from pkg_resources import resource_filename

from vegindex import config
from vegindex import ndvi_summary_timeseries

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

config.archive_dir = SAMPLE_DATA_DIR


def test_reading_ndvits_summary_file():
    """
    test reading in existing ndvits summary timeseries
    """

    sitename = "dukehw"
    roiname = "DB_1000"
    ndvi_file = "{}_{}_ndvi_3day.csv".format(sitename, roiname)

    # set up path to roistats file
    ndvi_path = os.path.join(SAMPLE_DATA_DIR, sitename, "ROI", ndvi_file)

    ndvits = ndvi_summary_timeseries.NDVISummaryTimeSeries(
        site=sitename, ROIListID=roiname
    )

    ndvits.readCSV(ndvi_path)
    first_row = ndvits.rows[0]
    last_row = ndvits.rows[-1]

    # test that we're getting header metadata correctly
    np.testing.assert_equal(ndvits.site, "dukehw")
    np.testing.assert_equal(ndvits.nday, 3)
    np.testing.assert_equal(ndvits.roitype, "DB")
    np.testing.assert_equal(ndvits.sequence_number, "1000")

    # spot check a couple of rows
    np.testing.assert_equal(
        last_row["midday_rgb_filename"], "dukehw_2020_07_15_115405.jpg"
    )
    np.testing.assert_equal(
        last_row["midday_ir_filename"], "dukehw_IR_2020_07_15_115405.jpg"
    )
    np.testing.assert_equal(first_row["ndvi_mean"], 0.22027)
    np.testing.assert_equal(first_row["ndvi_std"], 0.16966)
    np.testing.assert_equal(first_row["max_solar_elev"], 75.9963)
    np.testing.assert_equal(len(ndvits.rows), 870)
