# -*- coding: utf-8 -*-

__author__ = """Thomas Milliman"""
__email__ = 'thomas.milliman@unh.edu'
__version__ = '0.2.0rc1'

import os

from . import config

# from roimask import ROIMask
# from roilist import ROIList
# from roitimeseries import ROITimeSeries
# from gcctimeseries import GCCTimeSeries
# from quantile import quantile
# from vegindex import get_roi_list, get_roi_timeseries, \
#      get_gcc_timeseries, daterange2
# from utils import getsiteimglist

# root directory of data archive
if os.environ.get('PHENOCAM_ARCHIVE_DIR'):
    config.archive_dir = os.environ.get('PHENOCAM_ARCHIVE_DIR')
