# -*- coding: utf-8 -*-
"""
test_ir_roitimeseries
------------------

Tests for `vegindex.ir_roitimeseries` module.
"""

import os

import numpy as np
from PIL import Image
from pkg_resources import Requirement
from pkg_resources import resource_filename

from vegindex import config
from vegindex import ir_roitimeseries

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

config.archive_dir = SAMPLE_DATA_DIR


# def test_roits_dnmeans():
#     """
#     test calculating DN means from image/mask pair
#     """

#     image_file = 'alligatorriver_06_01_120032.jpg'
#     mask_file = 'alligatorriver_DB_0001_01.tif'
#     sitename, year, month, dom, xx = image_file.split('_')

#     image_path = os.path.join(SAMPLE_DATA_DIR, sitename, year,
#                               month, image_file)
#     mask_path = os.path.join(SAMPLE_DATA_DIR, sitename, 'ROI',
#                              mask_file)

#     im = Image.open(image_path)
#     roimask = Image.open(mask_path)

#     ir_mean, g_mean, b_mean, brt = ir_roitimeseries.get_dn_means(im,
#                                                                 roimask)

#     np.testing.assert_approx_equal(ir_mean, 48.82500, 3)


def test_ir_roits_roistats():
    """
    test calculating ROI IR stats from image/mask pair
    """

    image_file = "alligatorriver_IR_2013_06_01_120032.jpg"
    mask_file = "alligatorriver_DB_1000_01.tif"
    sitename, ir, year, month, dom, xx = image_file.split("_")

    image_path = os.path.join(SAMPLE_DATA_DIR, sitename, year, month, image_file)
    mask_path = os.path.join(SAMPLE_DATA_DIR, sitename, "ROI", mask_file)

    im = Image.open(image_path)
    roimask = Image.open(mask_path)

    ir_stats = ir_roitimeseries.get_roi_IR_stats(im, roimask)

    ir_mean = ir_stats["mean"]
    ir_sd = ir_stats["stdev"]
    ir_pcts = ir_stats["percentiles"]

    np.testing.assert_approx_equal(ir_mean, 91.24770, 3)
    np.testing.assert_approx_equal(ir_sd, 23.02635, 3)
    np.testing.assert_equal(ir_pcts[0], 50)
    np.testing.assert_equal(ir_pcts[6], 124)


def test_roits_metadata():
    """
    test reading IR image metadata
    """

    image_file = "alligatorriver_IR_2013_06_01_120032.meta"
    sitename, ir, year, month, dom, xx = image_file.split("_")
    image_path = os.path.join(SAMPLE_DATA_DIR, sitename, year, month, image_file)

    image_metadata = ir_roitimeseries.get_im_metadata(image_path)
    im_exposure = int(image_metadata["exposure"])
    np.testing.assert_equal(im_exposure, 14)


def test_reading_roits_file():
    """
    test reading in existing ir_roits timeseries
    """

    sitename = "alligatorriver"
    roiname = "DB_1000"
    roistats_file = "{}_{}_IR_roistats.csv".format(sitename, roiname)

    # set up path to roistats file
    roistats_path = os.path.join(SAMPLE_DATA_DIR, sitename, "ROI", roistats_file)

    roits = ir_roitimeseries.IRROITimeSeries(site=sitename, ROIListID=roiname)

    roits.readCSV(roistats_path)
    last_row = roits.rows[-1]

    np.testing.assert_equal(
        last_row["filename"], "alligatorriver_IR_2015_12_31_193031.jpg"
    )
    np.testing.assert_equal(last_row["exposure"], 2400)
