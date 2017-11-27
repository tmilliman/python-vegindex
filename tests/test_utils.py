# -*- coding: utf-8 -*-

"""
Tests for `vegindex.utils` module.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd

from vegindex import config
from vegindex import utils

config.archive_dir = os.path.join(os.path.dirname(__file__),
                                  "sample_data")

config.site_info_file = os.path.join(os.path.dirname(__file__),
                                  "sample_data","site_info.csv")

def test_fn2date():
    sitename = "harvard"
    rgb_file = "harvard_2009_06_30_120138.jpg"
    ir_file = "harvard_IR_2009_06_30_120138.jpg"

    datelist = utils.fn2date(sitename, rgb_file)
    assert datelist == [2009, 6, 30, 12, 1, 38]

    datelist = utils.fn2date(sitename, ir_file, irFlag=True)
    assert datelist == [2009, 6, 30, 12, 1, 38]


def test_fn2datetime():
    sitename = "harvard"
    rgb_file = "harvard_2009_06_30_120138.jpg"
    ir_file = "harvard_IR_2009_06_30_120138.jpg"

    dt = utils.fn2datetime(sitename, rgb_file)
    assert dt == datetime(2009, 6, 30, 12, 1, 38)

    dt = utils.fn2datetime(sitename, ir_file, irFlag=True)
    assert dt == datetime(2009, 6, 30, 12, 1, 38)


def test_getsiteimglist():
    """
    test getting list of images for a site"
    """

    # test existing sample directory
    sitename = "harvard"
    start_dt = datetime(2009, 6, 30)
    end_dt = datetime(2009, 7, 1)
    imglist = utils.getsiteimglist(sitename, startDT=start_dt,
                                   endDT=end_dt)
    assert len(imglist) == 1
    assert os.path.basename(imglist[0]) == "harvard_2009_06_30_120138.jpg"

    # test missing dir
    sitename = "acadia"
    imglist = utils.getsiteimglist(sitename, startDT=start_dt,
                                   endDT=end_dt)
    assert len(imglist) == 0


def test_get_siteinfo():
    """
    test getting site info from URL
    """

    sitename = 'harvard'
    siteinfo = utils.getsiteinfo(sitename)

    assert siteinfo['lon'] == -72.1715

def test_get_siteinfo_local():
    """
    test getting site info from CSV
    """

    sitename = 'test'
    siteinfo = utils.getsiteinfo(sitename)

    assert siteinfo['lon'] == -60


def test_deg2dms():

    deg = 60.504167
    dms = utils.deg2dms(deg)

    assert dms == "60:30:15"


def test_dms2deg():

    dmsstr = "60:30:15"
    dd = utils.dms2deg(dmsstr)
    np.testing.assert_approx_equal(dd, 60.504167, 5)


def test_sunelev():

    sunelev = -18.98094
    lon = -72.1715
    lat = 42.5378
    dt = datetime(2009, 1, 1, 5, 31, 34)
    offset = -5

    elev = utils.sunelev(lat, lon, dt, offset)
    np.testing.assert_approx_equal(elev, sunelev, 3)
