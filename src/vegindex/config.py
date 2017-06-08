# -*- coding: utf-8 -*-

# flag for dealing with IR images - by default
# we're not looking at IR images.
irFlag = False

# set default archive dir
archive_dir = '/data/archive'

# set up list of predefined ROITypes
ROITypes = ['canopy',
            'deciduous',
            'coniferous',
            'grass',
            'shrub',
            'modis',
            'refpanel',
            'misc',
            'tundra',
            'AG',
            'DB',
            'DN',
            'EB',
            'EN',
            'GR',
            'MX',
            'NV',
            'RF',
            'SH',
            'TN',
            'UN',
            'WL',
            'XX']

# set up image selection criteria for summary (gcc90 1-day
# and gcc90 3-day) files.

# set up selection for minimum Sun Elevation
MIN_SUN_ANGLE = 10.0

# set up selection for minimum and maximum brightness
MIN_BRT = 100
MAX_BRT = 665

# set up time-of-day restrictions
TIME_MIN = '00:00:00'
TIME_MAX = '23:59:59'

# set up minimum number of images for summary period
NIMAGE_MIN = 1

# set up default resize behavior
RESIZE = False

# set up no/missing data values
ND_FLOAT = 'NA'
ND_INT = 'NA'
ND_STRING = "None"

# ND_FLOAT = '-9999.'
# ND_INT = '-9999'
# ND_STRING = "None"
