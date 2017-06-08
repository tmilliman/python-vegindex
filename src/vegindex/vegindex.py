# -*- coding: utf-8 -*-

"""
Python Module for Vegetation Index Generation Routines
"""

import os
from datetime import date
from datetime import timedelta

from . import config
from .gcctimeseries import GCCTimeSeries
from .roilist import ROIList
from .roitimeseries import ROITimeSeries

# ********** Public Functions **************


def daterange2(start_date, end_date, nday):
    """
    make alternate daterange() function which uses fixed days
    of year between start_date and end_date.  In other words
    if nday=3 we always want the dates for doy=1,4,7, ...
    which fall between start and end dates.  Note: we start
    on the interval that includes the first date.
    """
    year_start = start_date.year
    year_end = end_date.year

    # loop over years and always use same doy intervals ...
    for iyear in range(year_start, year_end + 1, 1):

        # if this is the first year reset the start
        # date to the beginning of the first nday period
        # which includes start_date
        if iyear == year_start:
            doy_start = (start_date - date(iyear, 1, 1)).days + 1
            n = (doy_start - 1) / nday
            new_doy_start = n * nday + 1
            dstart = date(iyear, 1, 1) + timedelta(new_doy_start - 1)
        else:
            # start at the first day of year
            dstart = date(iyear, 1, 1)

        # if this is the last year, find the beginning
        # of the last nday period before the last date
        if iyear == year_end:
            doy_last = (end_date -
                        date(iyear, 1, 1)).days + 1
            n = (doy_last - 1) / nday
            new_doy_last = n * nday + 1
            dlast = date(iyear, 1, 1) + timedelta(new_doy_last - 1)

        else:
            doy_last = (date(iyear, 12, 31) -
                        date(iyear, 1, 1)).days + 1
            dlast = date(iyear, 12, 31)

        # for this year yield the first day of the next nday period
        for n in range(0, doy_last + 1, nday):
            dtval = dstart + timedelta(n)
            if ((dtval + timedelta(nday)) > start_date) and (dtval <= dlast):
                yield dtval


def get_roi_list(site, roilist_id):
    """
    function to read in CSV ROI file and return a ROIList object.
    """

    # take ROIList_id and parse into site, roitype, sequence_number
    (roitype, seqno_str) = roilist_id.split('_')
    sequence_number = int(seqno_str)

    # set cannonical dir for ROI Lists
    roidir = os.path.join(config.archive_dir, site, 'ROI')

    # set cannonical filename
    roifile = site + '_' + roilist_id + '_roi.csv'
    roipath = os.path.join(roidir, roifile)

    # create ROIList object
    roilist = ROIList(site=site, roitype=roitype,
                      sequence_number=sequence_number)

    # read in from CSV file
    roilist.readCSV(roipath)

    return roilist


def get_roi_timeseries(site, roilist_id):
    """
    function to read in CSV ROI file and return a ROITimeSeries object
    """

    # take ROIList_id and parse into site, roitype, sequence_number
    (roitype, seqno_str) = roilist_id.split('_')

    # set cannonical dir for ROI Lists
    roidir = os.path.join(config.archive_dir, site, 'ROI')

    # set cannonical filename
    roitsfile = site + '_' + roilist_id + '_timeseries.csv'
    roitspath = os.path.join(roidir, roitsfile)
    # print roitspath

    # create empty ROITimeSeries object
    roits = ROITimeSeries(site=site, ROIListID=roilist_id)

    # read in from CSV file
    roits.readCSV(roitspath)

    return roits


def get_gcc_timeseries(site, roilist_id, nday=3):
    """
    Read in CSV version of summary timeseries and return
    GCCTimeSeries object.
    """

    # take ROIList_id and parse into roitype, sequence_number
    (roitype, seqno_str) = roilist_id.split('_')

    # set cannonical dir for ROI Lists
    roidir = os.path.join(config.archive_dir, site, 'ROI')

    # set cannonical filename
    gcc_tsfile = site + '_' + roilist_id + '_{0}day.csv'.format(nday)
    gcc_tspath = os.path.join(roidir, gcc_tsfile)

    # create empty GCCTimeSeries object
    gccts = GCCTimeSeries(site=site, ROIListID=roilist_id)

    # read in from CSV file
    gccts.readCSV(gcc_tspath)

    return gccts
