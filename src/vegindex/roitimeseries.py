# -*- coding: utf-8 -*-
from __future__ import print_function

import csv
import os
import re
import sys
from datetime import datetime

import numpy as np
from PIL import Image

from . import config
from . import utils

ND_FLOAT = config.ND_FLOAT
ND_INT = config.ND_INT
ND_STRING = config.ND_STRING


def _float_or_none(str):
    """
    Try to convert string to float. Return float or None value if a
    ValueError exception is raised.
    """
    try:
        retval = float(str)
    except ValueError:
        retval = ND_FLOAT

    if retval == -9999.:
        retval = ND_FLOAT

    return retval


def _int_or_none(str):
    """
    Try to convert string to integer. Return int or None value
    if ValueError is raised.
    """
    try:
        retval = int(str)
    except ValueError:
        retval = ND_INT

    if retval == -9999:
        retval = ND_INT

    return retval

######################################################################


def get_dn_means(im, roimask):
    """
    Function to return mean DN values for an image / mask pair.
    NOTE: probably move this to utils.py.
    """

    # split into bands
    try:
        (im_r, im_g, im_b) = im.split()
    except:
        sys.stderr.write("Wrong image type\n")
        return None

    # create numpy arrays with bands
    r_array = np.asarray(im_r, dtype=np.float64)
    g_array = np.asarray(im_g, dtype=np.float64)
    b_array = np.asarray(im_b, dtype=np.float64)
    brt_array = r_array + g_array + b_array

    # try applying mask to red image ... if mask and image don't
    # have same size this will raise an exception.
    try:
        r_ma = np.ma.array(r_array, mask=roimask)
    except:
        errstr = "Error applying mask to image file.\n"
        sys.stderr.write(errstr)
        return None

    # make masked arrays for G,B
    g_ma = np.ma.array(g_array, mask=roimask)
    b_ma = np.ma.array(b_array, mask=roimask)

    # find mean values to store
    brt = np.mean(brt_array)
    g_mean_roi = np.mean(g_ma)
    r_mean_roi = np.mean(r_ma)
    b_mean_roi = np.mean(b_ma)

    return [r_mean_roi, g_mean_roi,  b_mean_roi, brt]


def get_roi_stats(im, roimask):
    """
    Function to return a more extensive collection of stats for DN
    values for an image / mask pair.  NOTE: probably move this to
    utils.py.
    """

    # split into bands
    try:
        (im_r, im_g, im_b) = im.split()
    except:
        sys.stderr.write("Wrong image type\n")
        return None

    # create numpy arrays with bands
    r_array = np.asarray(im_r, dtype=np.int16)
    g_array = np.asarray(im_g, dtype=np.int16)
    b_array = np.asarray(im_b, dtype=np.int16)
    brt_array = r_array + g_array + b_array

    # check that the image isn't nearly all black or all white in
    # which case getting the stats fails.  Eliminate the outer 30
    # pixels in case there is a banner/overlay on the image.
    #
    # NOTE: this is using almost entire image not just ROI

    if brt_array[30:-30, 30:-30].mean() < 30.0:
        warningstr = "WARNING: mostly dark image.\n"
        sys.stderr.write(warningstr)
        r_mean = ND_FLOAT
        r_std = ND_FLOAT
        r_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        g_mean = ND_FLOAT
        g_std = ND_FLOAT
        g_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        b_mean = ND_FLOAT
        b_std = ND_FLOAT
        b_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        RG_cor = ND_FLOAT
        GB_cor = ND_FLOAT
        BR_cor = ND_FLOAT
        return [{'mean': r_mean,
                 'stdev': r_std,
                 'percentiles': r_pcts},
                {'mean': g_mean,
                 'stdev': g_std,
                 'percentiles': g_pcts},
                {'mean': b_mean,
                 'stdev': b_std,
                 'percentiles': b_pcts},
                RG_cor, GB_cor, BR_cor]

    if brt_array[30:-30, 30:-30].mean() > 725.0:
        warningstr = "WARNING: mostly white image.\n"
        sys.stderr.write(warningstr)
        r_mean = ND_FLOAT
        r_std = ND_FLOAT
        r_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        g_mean = ND_FLOAT
        g_std = ND_FLOAT
        g_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        b_mean = ND_FLOAT
        b_std = ND_FLOAT
        b_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT,
                  ND_FLOAT, ND_FLOAT, ND_FLOAT]
        RG_cor = ND_FLOAT
        GB_cor = ND_FLOAT
        BR_cor = ND_FLOAT
        return [{'mean': r_mean,
                 'stdev': r_std,
                 'percentiles': r_pcts},
                {'mean': g_mean,
                 'stdev': g_std,
                 'percentiles': g_pcts},
                {'mean': b_mean,
                 'stdev': b_std,
                 'percentiles': b_pcts},
                RG_cor, GB_cor, BR_cor]

    # try applying mask to red image ... if mask and image don't
    # have same size this will raise an exception.
    try:
        r_ma = np.ma.array(r_array, mask=roimask)
    except Exception as inst:
        print(inst)
        errstr = "Error applying mask to image file.\n"
        sys.stderr.write(errstr)
        return None

    # make masked arrays for G,B
    g_ma = np.ma.array(g_array, mask=roimask)
    b_ma = np.ma.array(b_array, mask=roimask)

    # find mean and std values
    r_vals = r_ma.compressed()
    r_mean = r_vals.mean()
    r_diff = np.float64(r_vals) - r_mean
    r_std = np.sqrt(np.dot(r_diff, r_diff) / r_vals.size)

    g_vals = g_ma.compressed()
    g_mean = g_vals.mean()
    g_diff = np.float64(g_vals) - g_mean
    g_std = np.sqrt(np.dot(g_diff, g_diff) / g_vals.size)

    b_vals = b_ma.compressed()
    b_mean = b_vals.mean()
    b_diff = np.float64(b_vals) - b_mean
    b_std = np.sqrt(np.dot(b_diff, b_diff) / b_vals.size)

    # calculate percentiles for each array
    r_pcts = np.percentile(r_vals, (5., 10., 25., 50., 75., 90., 95.))
    g_pcts = np.percentile(g_vals, (5., 10., 25., 50., 75., 90., 95.))
    b_pcts = np.percentile(b_vals, (5., 10., 25., 50., 75., 90., 95.))

    # calculate covariance matrices and get cross-diagonal terms
    rg_cov = np.dot(r_diff, g_diff) / r_diff.size
    gb_cov = np.dot(g_diff, b_diff) / g_diff.size
    br_cov = np.dot(b_diff, r_diff) / b_diff.size

    # calculate correlation coefficient
    RG_cor = rg_cov / (r_std * g_std)
    GB_cor = gb_cov / (g_std * b_std)
    BR_cor = br_cov / (b_std * r_std)

    # if the above calculation can return a NaN then
    # I should probably trap that here and return a

    # return list of values
    return [{'mean': r_mean,
             'stdev': r_std,
             'percentiles': r_pcts},
            {'mean': g_mean,
             'stdev': g_std,
             'percentiles': g_pcts},
            {'mean': b_mean,
             'stdev': b_std,
             'percentiles': b_pcts},
            RG_cor, GB_cor, BR_cor]


def _filter_comments(f):
    """
    filter comments from csv file
    """
    for l in f:
        line = l.rstrip()
        if line and not line.startswith("#"):
            yield line


def _get_comments(f):
    """
    return JUST the comment lines from a csv file
    """
    for l in f:
        line = l.rstrip()
        if line and line.startswith("#"):
            yield line


def _get_comment_field(comments, var_string):
    """
    return value of a field from a list of comment lines

    The comment line with a field has the following format:

    # var_string: var_value

    For example:

    # Creation Date: 2012-02-01

    So we need to create a pattern, find a match and then return
    the value.  No checking of whether the value is valid will
    be done by this routine.
    """

    # set pattern to match
    pattern = '# {0}:\ (?P<var_value>.+)$'.format(var_string)

    var_value = ""
    for line in comments:

        result = re.match(pattern, line)

        if result is not None:
            var_value = result.group('var_value')
            break

    return var_value


class ROITimeSeries(object):
    """
    Class for CSV version of ROI Timeseries.  There is
    currently no equivalent dB table for an ROI time series
    object.

    Here's a proposed sample ROITimeSeries CSV file format:

        #
        # All-image time series for arbutuslake
        #
        # Site: arbutuslake
        # Veg Type: DB
        # ROI ID Number: arbutuslake_canopy_0001
        # Lat:
        # Lon:
        # Elev:
        # UTC Offset:
        # Resize Flag: False
        # Version: 1
        # Creation Date: 2013-03-29
        # Creation Time: 12:10:59
        # Update Date: 2013-03-29
        # Update Time: 14:16:43
        #
        date,local_std_time,doy,filename,solar_elev,exposure,mask_index,gcc,rcc,\
        r_mean,r_std,r_5_qtl,r_10_qtl,r_25_qtl,r_50_qtl,r_75_qtl,r_90_qtl,r_95_qtl,\
        g_mean,g_std,g_5_qtl,g_10_qtl,g_25_qtl,g_50_qtl,g_75_qtl,g_90_qtl,g_95_qtl,\
        b_mean,b_std,b_5_qtl,b_10_qtl,b_25_qtl,b_50_qtl,b_75_qtl,b_90_qtl,b_95_qtl,\
        r_g_correl,g_b_correl,b_r_correl
        2014-05-06,11:01:33,126,coweeta_2014_05_06_110133.jpg,62.96,-9999,2,
        92.25984,46.95709,24,39,62,86,116,154,181,\
        97.92024,44.42619,31,46,69,94,120,153,180,\
        31.40147,32.83882,0,0,4,25,45,72,95,\
        0.96995,0.89691,0.91008

    """

    def __init__(self, site='', ROIListID='', resizeFlag=False):
        """
        create ROITimeSeries object
        """

        self.site = site
        self.roilistid = ROIListID
        # self.irFlg = irFlag
        self.resizeFlg = resizeFlag
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.rows = []

        # split ROIListID into roitype, and sequence_number
        roitype, sequence_number = ROIListID.split('_')
        self.roitype = roitype
        self.sequence_number = int(sequence_number)

        # grab site info ... really should be a separate
        # class for site with all the site info ... should
        # figure out how to use Django classes here
        if site:
            try:
                si = utils.getsiteinfo(site)
            except:
                si = {'lat': None,
                      'lon': None,
                      'elev': None,
                      'tzoffset': None}
        else:
            si = {'lat': None,
                  'lon': None,
                  'elev': None,
                  'tzoffset': None}

        self.lat = si['lat']
        self.lon = si['lon']
        self.elev = si['elev']
        self.tzoffset = si['tzoffset']

    def get_image_list(self):
        """
        return list of images in an ROI timeseries
        """
        imglist = [row['filename'] for row in self.rows]

        return imglist

    def create_row(self, impath, roimask, mask_index):
        """
        create a ROITimeSeries row dictionary for a given image and
        ROI mask.
        """

        # extract datetime from filename
        img_file = os.path.basename(impath)
        img_DT = utils.fn2datetime(self.site, img_file, irFlag=False)
        img_date = img_DT.date()
        img_time = img_DT.time()

        # get doy
        # img_doy = img_DT.timetuple().tm_yday

        # find sun elevation (degrees)
        sun_elev = utils.sunelev(self.lat, self.lon, img_DT, self.tzoffset)

        # Try to load image
        try:
            im = Image.open(impath, 'r')
            im.load()
        except:
            errstr1 = "Unable to open file: %s\n" % (impath,)
            errstr2 = "Skipping this file.\n"
            sys.stderr.write(errstr1)
            sys.stderr.write(errstr2)
            return None

        # if resizeFlg is True resize image to match mask
        if self.resizeFlg:
            ysize, xsize = roimask.shape
            if (xsize, ysize) != im.size:
                warnmsg = "Resizing image {0} to match mask.\n"
                warnmsg = warnmsg.format(img_file)
                sys.stdout.write(warnmsg)
                im = im.resize((xsize, ysize), Image.ANTIALIAS)

        # find mean values over ROI
        try:
            # [dn_r, dn_g, dn_b, brt] = get_dn_means(im, roimask)
            roistats_list = get_roi_stats(im, roimask)

        except KeyboardInterrupt:
            sys.exit()
        except Exception as inst:
            print(inst)
            errstr1 = "Problem getting ROI " + \
                      "stats for file in create_row(): {0}\n".format(impath)
            sys.stderr.write(errstr1)
            return None

        # get_dn_stats returns None if can't get stats (probably
        # should just throw exception in which case it would be caught
        # by above except clause

        if not(roistats_list):
            return None

        # extract stats
        r_stats = roistats_list[0]
        g_stats = roistats_list[1]
        b_stats = roistats_list[2]
        rg_cor = roistats_list[3]
        gb_cor = roistats_list[4]
        br_cor = roistats_list[5]

        r_mean = r_stats['mean']
        r_std = r_stats['stdev']
        # r_pcts = r_stats['percentiles']
        r_5, r_10, r_25, r_50, r_75, r_90, r_95 = r_stats['percentiles']

        g_mean = g_stats['mean']
        g_std = g_stats['stdev']
        # g_pcts = g_stats['percentiles']
        g_5, g_10, g_25, g_50, g_75, g_90, g_95 = g_stats['percentiles']

        b_mean = b_stats['mean']
        b_std = b_stats['stdev']
        # b_pcts = b_stats['percentiles']
        b_5, b_10, b_25, b_50, b_75, b_90, b_95 = b_stats['percentiles']

        if r_mean != ND_FLOAT:
            brt_mean = r_mean + g_mean + b_mean
        else:
            brt_mean = ND_FLOAT

        if brt_mean > 0 and brt_mean != ND_FLOAT:
            gcc = g_mean / brt_mean
            rcc = r_mean / brt_mean
        else:
            gcc = ND_FLOAT
            rcc = ND_FLOAT

        # get exposure - just set to missing value for now
        exposure = ND_INT

        # make a structure for the roi timeseries
        roits_row = {'date': img_date,
                     'local_std_time': img_time,
                     'datetime': img_DT,
                     'r_mean': r_mean,
                     'r_std': r_std,
                     'r_5_qtl': r_5,
                     'r_10_qtl': r_10,
                     'r_25_qtl': r_25,
                     'r_50_qtl': r_50,
                     'r_75_qtl': r_75,
                     'r_90_qtl': r_90,
                     'r_95_qtl': r_95,

                     'g_mean': g_mean,
                     'g_std': g_std,
                     'g_5_qtl': g_5,
                     'g_10_qtl': g_10,
                     'g_25_qtl': g_25,
                     'g_50_qtl': g_50,
                     'g_75_qtl': g_75,
                     'g_90_qtl': g_90,
                     'g_95_qtl': g_95,

                     'b_mean': b_mean,
                     'b_std': b_std,
                     'b_5_qtl': b_5,
                     'b_10_qtl': b_10,
                     'b_25_qtl': b_25,
                     'b_50_qtl': b_50,
                     'b_75_qtl': b_75,
                     'b_90_qtl': b_90,
                     'b_95_qtl': b_95,

                     'r_g_correl': rg_cor,
                     'g_b_correl': gb_cor,
                     'b_r_correl': br_cor,

                     'gcc': gcc,
                     'rcc': rcc,
                     'filename': '%s' % (img_file,),
                     'mask_index': mask_index,
                     'solar_elev': sun_elev,
                     'exposure': exposure}

        return roits_row

    def insert_row(self, impath, roimask, mask_index):
        """
        create a ROITimeSeries row dictionary and insert it into
        self.rows list and return the row dictionary.  If there is
        a problem creating the row return None.
        """

        # create row dictionary
        roits_row = self.create_row(impath, roimask, mask_index)
        if not roits_row:
            return None

        # use file name as key, only one row per image file
        rowfn = roits_row['filename']
        FN_INDEX = [row['filename'] for row in self.rows]
        try:
            row_index = FN_INDEX.index(rowfn)
        except:
            row_index = None

        # replace or append
        if row_index:
            self.rows.pop(row_index)
            self.rows.append(roits_row)
        else:
            self.rows.append(roits_row)

        return roits_row

    def append_row(self, impath, roimask, mask_index):
        """
        create a ROITimeSeries row dictionary and append it to
        self.rows list and return the row dictionary.
        """

        # create row dictionary
        roits_row = self.create_row(impath, roimask, mask_index)

        # append row
        if roits_row:
            self.rows.append(roits_row)

        return roits_row

    def format_csvrow(self, roits_row):
        """
        format ROITimeSeries CSV row as string
        """

        row_dt = roits_row['datetime']
        row_doy = row_dt.timetuple().tm_yday

        r_pcts = [roits_row['r_5_qtl'], roits_row['r_10_qtl'],
                  roits_row['r_25_qtl'], roits_row['r_50_qtl'],
                  roits_row['r_75_qtl'], roits_row['r_90_qtl'],
                  roits_row['r_95_qtl']]

        g_pcts = [roits_row['g_5_qtl'], roits_row['g_10_qtl'],
                  roits_row['g_25_qtl'], roits_row['g_50_qtl'],
                  roits_row['g_75_qtl'], roits_row['g_90_qtl'],
                  roits_row['g_95_qtl']]

        b_pcts = [roits_row['b_5_qtl'], roits_row['b_10_qtl'],
                  roits_row['b_25_qtl'], roits_row['b_50_qtl'],
                  roits_row['b_75_qtl'], roits_row['b_90_qtl'],
                  roits_row['b_95_qtl']]

        csvstr_0 = '{},{},{},{},{:.5f},{},{}'
        csvstr_0 = csvstr_0.format(roits_row['date'],
                                   roits_row['local_std_time'],
                                   row_doy,
                                   roits_row['filename'],
                                   roits_row['solar_elev'],
                                   roits_row['exposure'],
                                   roits_row['mask_index'])

        if roits_row['gcc'] == ND_FLOAT:
            csvfmt = '{},{}'
        else:
            csvfmt = '{:.5f},{:.5f}'
        csvstr_1 = csvfmt.format(roits_row['gcc'],
                                 roits_row['rcc'])

        # red
        if roits_row['r_mean'] == ND_FLOAT:
            csvfmt = '{},{}'
        else:
            csvfmt = '{:.5f},{:.5f}'
        csvstr_2 = csvfmt.format(roits_row['r_mean'],
                                 roits_row['r_std'])
        if r_pcts[0] == ND_FLOAT:
            csvfmt = '{}'
        else:
            csvfmt = '{:.0f}'
        csvstr_3 = ','.join(csvfmt.format(k) for k in r_pcts)

        # green
        if roits_row['g_mean'] == ND_FLOAT:
            csvfmt = '{},{}'
        else:
            csvfmt = '{:.5f},{:.5f}'
        csvstr_4 = csvfmt.format(roits_row['g_mean'],
                                 roits_row['g_std'])
        if g_pcts[0] == ND_FLOAT:
            csvfmt = '{}'
        else:
            csvfmt = '{:.0f}'
        csvstr_5 = ','.join(csvfmt.format(k) for k in g_pcts)

        # blue
        if roits_row['b_mean'] == ND_FLOAT:
            csvfmt = '{},{}'
        else:
            csvfmt = '{:.5f},{:.5f}'
        csvstr_6 = csvfmt.format(roits_row['b_mean'],
                                 roits_row['b_std'])
        if b_pcts[0] == ND_FLOAT:
            csvfmt = '{}'
        else:
            csvfmt = '{:.0f}'
        csvstr_7 = ','.join(csvfmt.format(k) for k in b_pcts)

        # csvstr_4 = '{0:.5f},{1:.5f}'.format(roits_row['g_mean'],
        #                                     roits_row['g_std'])
        # csvstr_5 = ','.join('{0:.0f}'.format(k) for k in g_pcts)

        # csvstr_6 = '{0:.5f},{1:.5f}'.format(roits_row['b_mean'],
        #                                     roits_row['b_std'])
        # csvstr_7 = ','.join('{0:.0f}'.format(k) for k in b_pcts)

        if (
            (roits_row['r_g_correl'] == ND_FLOAT) or
            (roits_row['g_b_correl'] == ND_FLOAT) or
            (roits_row['b_r_correl'] == ND_FLOAT)
        ):

            csvfmt = '{},{},{}'
        else:
            csvfmt = '{0:.5f},{1:.5f},{2:.5f}'

        csvstr_8 = csvfmt.format(roits_row['r_g_correl'],
                                 roits_row['g_b_correl'],
                                 roits_row['b_r_correl'])

        csvstr = ','.join([csvstr_0, csvstr_1, csvstr_2, csvstr_3, csvstr_4,
                           csvstr_5, csvstr_6, csvstr_7, csvstr_8])

        return csvstr

    def writeCSV(self, file=""):
        """
        Method for writing an ROITimeSeries to CSV file.  The method
        opens the file for writing.  If no filename is passed
        then write to stdout.
        """
        if file == "":
            fo = sys.stdout
        else:
            fo = open(file, 'w')

        # write header
        hdstrings = []
        hdstrings.append('#\n')
        hdstrings.append('# All-image time series for {0}\n'.format(self.site))
        hdstrings.append('#\n')
        hdstrings.append('# Site: {0}\n'.format(self.site))
        hdstrings.append('# Veg Type: {0}\n'.format(self.roitype))
        hdstrings.append('# ROI ID Number: {0:04d}\n'.format(
            self.sequence_number))
        hdstrings.append('# Lat: {0}\n'.format(self.lat))
        hdstrings.append('# Lon: {0}\n'.format(self.lon))
        hdstrings.append('# Elev: {0}\n'.format(self.elev))
        hdstrings.append('# UTC Offset: {0}\n'.format(self.tzoffset))
        hdstrings.append('# Resize Flag: {0}\n'.format(self.resizeFlg))
        hdstrings.append('# Version: 1\n')
        hdstrings.append('# Creation Date: {0}\n'.
                         format(self.created_at.date()))
        create_time = self.created_at.time()
        hdstrings.append('# Creation Time: {0:02d}:{1:02d}:{2:02d}\n'.
                         format(create_time.hour,
                                create_time.minute,
                                create_time.second))

        # set update date and time
        self.updated_at = datetime.now()
        update_time = self.updated_at.time()
        hdstrings.append('# Update Date: {0}\n'.
                         format(self.updated_at.date()))
        hdstrings.append('# Update Time: {0:02d}:{1:02d}:{2:02d}\n'.
                         format(update_time.hour,
                                update_time.minute,
                                update_time.second))
        hdstrings.append('#\n')
        for line in hdstrings:
            fo.write(line)

        # write fields line
        fields_str = 'date,local_std_time,doy,filename,' + \
                     'solar_elev,exposure,' + \
                     'mask_index,gcc,rcc,' + \
                     'r_mean,r_std,r_5_qtl,r_10_qtl,r_25_qtl,r_50_qtl,' + \
                     'r_75_qtl,r_90_qtl,r_95_qtl,' + \
                     'g_mean,g_std,g_5_qtl,g_10_qtl,g_25_qtl,g_50_qtl,' + \
                     'g_75_qtl,g_90_qtl,g_95_qtl,' + \
                     'b_mean,b_std,b_5_qtl,b_10_qtl,b_25_qtl,b_50_qtl,' + \
                     'b_75_qtl,b_90_qtl,b_95_qtl,' + \
                     'r_g_correl,g_b_correl,b_r_correl\n'
        fo.write(fields_str)

        # sort rows by datetime before writing
        rows = self.rows
        rows_sorted = sorted(rows, key=lambda k: k['datetime'])
        self.rows = rows_sorted

        # print rows in timeseries
        nout = 0
        for row in self.rows:
            rowstr = self.format_csvrow(row)
            fo.write("{0}\n".format(rowstr))
            nout += 1

        # close output
        if not file == "":
            fo.close()

        return nout

    def select_rows(self, tod_min=config.TIME_MIN, tod_max=config.TIME_MAX,
                    sunelev_min=config.MIN_SUN_ANGLE, brt_min=config.MIN_BRT,
                    brt_max=config.MAX_BRT):
        """
        routine to return a list of the rows in self.rows
        which meet the selection criteria for brightness
        and time of day.  Numpy probably has a better (i.e. faster)
        way to do this. Also remove rows where thie image is
        completely black.
        """
        selected_rows = []
        for row in self.rows:
            brt = row['r_mean'] + row['g_mean'] + row['b_mean']
            if (row['datetime'].time() < tod_min) or \
               (row['datetime'].time() > tod_max) or \
               (brt < brt_min) or \
               (brt > brt_max) or \
               (row['solar_elev'] < sunelev_min):
                continue
            else:
                selected_rows.append(row)

        rows = sorted(selected_rows, key=lambda k: k['datetime'])

        return rows

    def readCSV(self, roiTimeSeriesPath):
        """
        Method to read ROITimeSeries object from CSV file and return
        a ROITimeSeries object.  If the comment fields are not present
        they must be set before the object can be written.
        """

        # open file for reading
        f = open(roiTimeSeriesPath, 'r')

        # get comment lines
        comments = list(_get_comments(f))

        # no validation applied to sitename
        site = _get_comment_field(comments, 'Site')
        if site != "":
            self.site = site

        # no validataion applied to ROIListId
        # roilistid = _get_comment_field(comments, 'ROI-id')
        # if roilistid != "":
        #     self.roilistid = roilistid
        roitype = _get_comment_field(comments, 'Veg Type')
        roiseqno = _get_comment_field(comments, 'ROI ID Number')
        self.roitype = roitype
        self.sequence_number = int(roiseqno)
        self.roilistid = "{0}_{1:04d}".format(roitype, int(roiseqno))

        # get Resize Flag if found in header
        resizeflg = _get_comment_field(comments, 'Resize Flag')
        if resizeflg != "":
            # convert to boolean
            if resizeflg == 'True':
                self.resizeFlg = True

        # make sure we can form a proper date time from create_date and
        # create_time
        create_date = _get_comment_field(comments, 'Creation Date')
        create_time = _get_comment_field(comments, 'Creation Time')
        if create_date != "" and create_time != "":
            try:
                (Y, M, D) = create_date.split('-')
                (h, m, s) = create_time.split(':')
                create_dt = datetime(int(Y), int(M), int(D), int(h),
                                     int(m), int(s))
                self.created_at = create_dt
            except ValueError:
                print("Invalid creation date or time in CSV.")

        # make sure we can form a proper date time from update_date and
        # update_time
        update_date = _get_comment_field(comments, 'Update Date')
        update_time = _get_comment_field(comments, 'Update Time')
        if update_date != "" and update_time != "":
            try:
                (Y, M, D) = update_date.split('-')
                (h, m, s) = update_time.split(':')
                update_dt = datetime(int(Y), int(M), int(D), int(h),
                                     int(m), int(s))
                self.updated_at = update_dt
            except ValueError:
                print("Invalid update date or time in CSV.")

        # do I need to grab lat, lon, elev and tzoffset?  Probably!

        # get timeseries rows
        f.seek(0)
        csvrdr = csv.DictReader(_filter_comments(f))

        roitsRows = []
        for row in csvrdr:

            # turn date and time strings into datetime values
            (im_yr, im_mo, im_dom) = row['date'].split('-')
            (im_hr, im_min, im_sec) = row['local_std_time'].split(':')
            im_dt = datetime(int(im_yr), int(im_mo), int(im_dom),
                             int(im_hr), int(im_min), int(im_sec))

            row['datetime'] = im_dt

            # convert strings to numbers - there's got to be a more
            # efficient way to do this!
            row['solar_elev'] = _float_or_none(row['solar_elev'])
            row['exposure'] = _int_or_none(_float_or_none(row['exposure']))
            row['mask_index'] = _int_or_none(row['mask_index'])
            row['gcc'] = _float_or_none(row['gcc'])
            row['rcc'] = _float_or_none(row['rcc'])
            row['r_mean'] = _float_or_none(row['r_mean'])
            row['r_std'] = _float_or_none(row['r_std'])
            row['r_5_qtl'] = _float_or_none(row['r_5_qtl'])
            row['r_10_qtl'] = _float_or_none(row['r_10_qtl'])
            row['r_25_qtl'] = _float_or_none(row['r_25_qtl'])
            row['r_50_qtl'] = _float_or_none(row['r_50_qtl'])
            row['r_75_qtl'] = _float_or_none(row['r_75_qtl'])
            row['r_90_qtl'] = _float_or_none(row['r_90_qtl'])
            row['r_95_qtl'] = _float_or_none(row['r_95_qtl'])
            row['g_mean'] = _float_or_none(row['g_mean'])
            row['g_std'] = _float_or_none(row['g_std'])
            row['g_5_qtl'] = _float_or_none(row['g_5_qtl'])
            row['g_10_qtl'] = _float_or_none(row['g_10_qtl'])
            row['g_25_qtl'] = _float_or_none(row['g_25_qtl'])
            row['g_50_qtl'] = _float_or_none(row['g_50_qtl'])
            row['g_75_qtl'] = _float_or_none(row['g_75_qtl'])
            row['g_90_qtl'] = _float_or_none(row['g_90_qtl'])
            row['g_95_qtl'] = _float_or_none(row['g_95_qtl'])
            row['b_mean'] = _float_or_none(row['b_mean'])
            row['b_std'] = _float_or_none(row['b_std'])
            row['b_5_qtl'] = _float_or_none(row['b_5_qtl'])
            row['b_10_qtl'] = _float_or_none(row['b_10_qtl'])
            row['b_25_qtl'] = _float_or_none(row['b_25_qtl'])
            row['b_50_qtl'] = _float_or_none(row['b_50_qtl'])
            row['b_75_qtl'] = _float_or_none(row['b_75_qtl'])
            row['b_90_qtl'] = _float_or_none(row['b_90_qtl'])
            row['b_95_qtl'] = _float_or_none(row['b_95_qtl'])
            row['r_g_correl'] = _float_or_none(row['r_g_correl'])
            row['g_b_correl'] = _float_or_none(row['g_b_correl'])
            row['b_r_correl'] = _float_or_none(row['b_r_correl'])
            roitsRows.append(row)

        # do I need to sort here?

        self.rows = roitsRows
        f.close()
