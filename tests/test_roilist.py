# -*- coding: utf-8 -*-

"""
test_roilist
----------------------------------

Tests for `vegindex.roilist` module.
"""

from __future__ import print_function

import os

import pytest

from vegindex import config
from vegindex import roilist

# MODULE_DIR = os.path.dirname(vegindex.__file__)
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__),
                               'sample_data')


def test_roilist_creation():
    """
    basic ROIlist creation
    """

    mylist = roilist.ROIList(site='testsite',
                             roitype='DB',
                             descrip='test ROI',
                             sequence_number=1,
                             owner='phenocam')

    assert mylist.roitype == 'DB'
    assert mylist.site == 'testsite'
    assert mylist.sequence_number == 1
    assert mylist.owner == 'phenocam'
    assert mylist.namestring() == 'testsite_DB_0001'
    assert mylist.__unicode__() == u'testsite_DB_0001'
    assert len(mylist.masks) == 0


def test_roilist_vegtype():
    """
    try creating a list with an unsupported veg_type
    """

    with pytest.raises(ValueError):
        mylist = roilist.ROIList(site='testsite',
                                 roitype='DE',
                                 descrip='test ROI',
                                 sequence_number=1,
                                 owner='phenocam')
        print(mylist)


def test_roilist_readcsv():
    """
    test reading a sample ROIList file
    """

    roilist_site = 'harvard'
    roilist_file = 'harvard_DB_0001_roi.csv'
    roilist_path = os.path.join(SAMPLE_DATA_DIR,
                                roilist_site,
                                'ROI',
                                roilist_file)

    mylist = roilist.ROIList()
    mylist.readCSV(roilist_path)
    assert mylist.site == 'harvard'
    assert mylist.roitype == 'DB'
    assert mylist.sequence_number == 1
    assert len(mylist.masks) == 1
