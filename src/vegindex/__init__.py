# -*- coding: utf-8 -*-

__author__ = """Thomas Milliman"""
__email__ = "thomas.milliman@unh.edu"
__version__ = "0.7.2"

import os

from . import config

# root directory of data archive
if os.environ.get("PHENOCAM_ARCHIVE_DIR"):
    config.archive_dir = os.environ.get("PHENOCAM_ARCHIVE_DIR")

# local site information file
if os.environ.get("PHENOCAM_SITE_INFO"):
    config.site_info_file = os.environ.get("PHENOCAM_SITE_INFO")
