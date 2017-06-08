# -*- coding: utf-8 -*-

"""
test_roitimeseries
------------------

Tests for `vegindex.roitimeseries` module.
"""

import os

import numpy as np
from PIL import Image
from pkg_resources import Requirement
from pkg_resources import resource_filename

from vegindex import config
from vegindex import roitimeseries

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__),
                               'sample_data')


def test_roits_dnmeans():
    """
    test calculating DN means from image/mask pair
    """

    image_file = 'harvard_2009_06_30_120138.jpg'
    mask_file = 'harvard_DB_0001_01.tif'
    sitename, year, month, dom, xx = image_file.split('_')

    image_path = os.path.join(SAMPLE_DATA_DIR, sitename, year,
                              month, image_file)
    mask_path = os.path.join(SAMPLE_DATA_DIR, sitename, 'ROI',
                             mask_file)

    im = Image.open(image_path)
    roimask = Image.open(mask_path)

    r_mean, g_mean, b_mean, brt = roitimeseries.get_dn_means(im,
                                                             roimask)

    np.testing.assert_approx_equal(r_mean, 48.82500, 3)
    np.testing.assert_approx_equal(g_mean, 69.22912, 3)
    np.testing.assert_approx_equal(b_mean, 42.85413, 3)
    np.testing.assert_approx_equal(brt, 310.30830, 3)


def test_roits_roistats():
    """
    test calculating ROI stats from image/mask pair
    """

    image_file = 'harvard_2009_06_30_120138.jpg'
    mask_file = 'harvard_DB_0001_01.tif'
    sitename, year, month, dom, xx = image_file.split('_')

    image_path = os.path.join(SAMPLE_DATA_DIR, sitename, year,
                              month, image_file)
    mask_path = os.path.join(SAMPLE_DATA_DIR, sitename, 'ROI',
                             mask_file)

    im = Image.open(image_path)
    roimask = Image.open(mask_path)

    [r_stats, g_stats, b_stats, RG_cor, GB_cor,
     BR_cor] = roitimeseries.get_roi_stats(im, roimask)

    r_mean = r_stats['mean']
    r_sd = r_stats['stdev']
    r_pcts = r_stats['percentiles']
    print r_pcts
    g_mean = g_stats['mean']
    g_sd = g_stats['stdev']
    g_pcts = g_stats['percentiles']
    b_mean = b_stats['mean']
    b_sd = b_stats['stdev']
    b_pcts = b_stats['percentiles']

    np.testing.assert_approx_equal(r_mean, 48.82500, 3)
    np.testing.assert_approx_equal(r_sd, 29.08593, 3)
    np.testing.assert_equal(r_pcts[0], 9)
    np.testing.assert_equal(r_pcts[6], 102)
    np.testing.assert_approx_equal(g_mean, 69.22912, 3)
    np.testing.assert_approx_equal(g_sd, 32.44997, 3)
    np.testing.assert_approx_equal(b_mean, 42.85413, 3)
    np.testing.assert_approx_equal(b_sd, 27.45573, 3)
    np.testing.assert_approx_equal(RG_cor, 0.975, 3)
    np.testing.assert_approx_equal(GB_cor, 0.944, 3)
    np.testing.assert_approx_equal(BR_cor, 0.964, 3)
