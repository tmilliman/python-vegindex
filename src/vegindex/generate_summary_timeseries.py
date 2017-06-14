# -*- coding: utf-8 -*-

"""
Script to generate a csv with summary files from a roi
timeseries csv file.  Output format will be:

date,year,doy,image_count,midday_filename,midday_r,midday_g,midday_b,midday_gcc,midday_rcc,
r_mean,r_std,g_mean,g_std,b_mean,b_std,gcc_mean,gcc_std,gcc_50,gcc_75,gcc_90,rcc_mean,
rcc_std,rcc_50,rcc_75,rcc_90,max_solar_elev,snow_flag,outlierflag_gcc_mean,
outlierflag_gcc_50,outlierflag_gcc_75,outlierflag_gcc_90
2008-04-04,04:01:40,95,harvard_2008_04_04_040140.jpg,-15.59448,-9999.0,1,0.18285
,24.76647,2.61462,20,22,23,25,26,28,29,11.22271,2.51949,7,8,10,11,13,14,15,25.38
766,2.74048,21,22,24,26,27,29,30,0.87536,0.84553,0.83233,50.,-9999,-9999,-9999,-9999,
-9999
2008-04-04,04:31:40,95,harvard_2008_04_04_043140.jpg,-10.42516,-9999.0,1,0.18382
,24.78447,2.62504,20,22,23,25,26,28,29,11.25862,2.54794,7,8,10,11,13,14,15,25.20
662,2.80735,20,22,24,25,27,28,29,0.88964,0.83442,0.82846,50.,-9999,-9999,-9999,-9999,
-9999

At some point we need to account for missing data.  One way would be
to make an empty row for that date.

2008-04-06,,,,,,,,,,,,,,,,

The following image selection parameters are read from a config file
(if it's present) or set to a default if not.  Only values changed
from defaults need to be in the config file.

default_nimage_threshold=1
default_time_min='00:00:00'
default_time_max='23:59:59'

Here's a sample config file which should be named
<sitename>_<roi-id>_gcc90.cfg and be in the ROI directory
of the data archive for the site:

----start of file----
[gcc90_calculation]
brt_threshold_min=160

----end of file----

You can specify any of the above parameters to configure
image selection in the gcc90 calculations.

"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
from datetime import datetime
from datetime import time
from datetime import timedelta

import numpy as np

import vegindex as vi
from vegindex.gcctimeseries import GCCTimeSeries
from vegindex.vegindex import daterange2
from vegindex.vegindex import get_roi_timeseries

from .quantile import quantile

try:
    import configparser
except:
    from ConfigParser import SafeConfigParser as configparser

# set vars

# you can set the archive directory to somewhere else for testing by
# using the env variable, PHENOCAM_ARCHIVE_DIR.
archive_dir = vi.config.archive_dir

# set missing/no-data values
ND_FLOAT = vi.config.ND_FLOAT
ND_INT = vi.config.ND_INT
ND_STRING = vi.config.ND_STRING

irflg = False
debug = False

# get default image selectors
default_nimage_threshold = vi.config.NIMAGE_MIN
default_time_min = vi.config.TIME_MIN
default_time_max = vi.config.TIME_MAX
default_sunelev_min = vi.config.MIN_SUN_ANGLE
default_brt_min = vi.config.MIN_BRT
default_brt_max = vi.config.MAX_BRT


def main():

    # set up command line argument processing
    parser = argparse.ArgumentParser()

    # options
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true",
                        default=False)
    parser.add_argument("-n", "--dry-run",
                        help="Process data but don't save results",
                        action="store_true",
                        default=False)

    parser.add_argument("-p", "--aggregation-period",
                        help="Number of Days to Aggregate (default=1)",
                        nargs='?', type=int, choices=range(1, 5, 2),
                        default=1)

    # positional arguments
    parser.add_argument("site", help="PhenoCam site name")
    parser.add_argument("roiname", help="ROI name, e.g. canopy_0001")

    # get args
    args = parser.parse_args()
    sitename = args.site
    roiname = args.roiname
    verbose = args.verbose
    dryrun = args.dry_run
    ndays = args.aggregation_period

    if verbose:
        print("site: {0}".format(sitename))
        print("roiname: {0}".format(roiname))
        print("verbose: {0}".format(verbose))
        print("dryrun: {0}".format(dryrun))
        print("period: {0}".format(ndays))

    # read in config file for this ROI List if it exists
    config_file = "{0}_{1}.cfg".format(sitename, roiname)
    config_path = os.path.join(archive_dir, sitename, 'ROI',
                               config_file)
    if os.path.exists(config_path):
        # NOTE: should probably subclass safe config parser
        # and add gettime() method which checks for time validity
        cfgparser = configparser(
            defaults={'nimage_threshold': str(default_nimage_threshold),
                      'time_min': str(default_time_min),
                      'time_max': str(default_time_max),
                      'sunelev_min': str(default_sunelev_min),
                      'brt_min': str(default_brt_min),
                      'brt_max': str(default_brt_max)})

        cfgparser.read(config_path)

        if cfgparser.has_section('gcc90_calculation'):
            nimage_threshold = cfgparser.getint('gcc90_calculation',
                                                'nimage_threshold')
            time_max_str = cfgparser.get('gcc90_calculation',
                                         'time_max')
            [tmax_hr, tmax_mn, tmax_sc] = time_max_str.split(':')
            time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
            time_min_str = cfgparser.get('gcc90_calculation',
                                         'time_min')
            [tmin_hr, tmin_mn, tmin_sc] = time_min_str.split(':')
            time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
            sunelev_min = cfgparser.getfloat('gcc90_calculation',
                                             'sunelev_min')
            brt_min = cfgparser.getint('gcc90_calculation', 'brt_min')
            brt_max = cfgparser.getint('gcc90_calculation', 'brt_max')
        else:
            nimage_threshold = int(default_nimage_threshold)
            [tmax_hr, tmax_mn, tmax_sc] = default_time_max.split(':')
            time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
            [tmin_hr, tmin_mn, tmin_sc] = default_time_min.split(':')
            time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
            sunelev_min = default_sunelev_min
            brt_min = default_brt_min
            brt_max = default_brt_max

    else:
        nimage_threshold = int(default_nimage_threshold)
        [tmax_hr, tmax_mn, tmax_sc] = default_time_max.split(':')
        time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
        [tmin_hr, tmin_mn, tmin_sc] = default_time_min.split(':')
        time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
        sunelev_min = default_sunelev_min
        brt_min = default_brt_min
        brt_max = default_brt_max

    # print config values
    if verbose:
        print('')
        print('gcc config:')
        print('===========')
        print('roi_list: ', '{0}_{1}_roi.csv'.format(sitename, roiname))
        if os.path.exists(config_path):
            print("config file: {0}".format(config_file))
        else:
            print("config file: None")
        print('nimage threshold: ', nimage_threshold)
        print('time of day min: ', time_min)
        print('time of day max: ', time_max)
        print('sun elev min: ', sunelev_min)
        print('aggregate days: ', ndays)
        print('minimum brightness: ', brt_min)
        print('maximum brightness: ', brt_max)

    # set up output filename
    outdir = os.path.join(archive_dir, sitename, 'ROI')
    outfile = '{0}_{1}_{2}day.csv'.format(sitename, roiname, ndays)
    outpath = os.path.join(outdir, outfile)
    if verbose:
        print('output file: ', outfile)

    # create gcc timeseries object as empty list
    gcc_ts = GCCTimeSeries(site=sitename, ROIListID=roiname,
                           nday=ndays,
                           nmin=nimage_threshold,
                           tod_min=time_min,
                           tod_max=time_max,
                           sunelev_min=sunelev_min,
                           brt_min=brt_min,
                           brt_max=brt_max)

    # get roi timeseries for this site and roi
    roits = get_roi_timeseries(sitename, roiname)

    if verbose:
        print('')
        print('ROI timeseries info:')
        print('====================')
        print('site: ', roits.site)
        print('ROI list id: ', roits.roilistid)
        print('create date: ', roits.created_at)
        print('update date: ', roits.updated_at)
        print('nrows: ', len(roits.rows))

    # make list of rows which match image selection criteria
    roits_rows = roits.select_rows(tod_min=time_min,
                                   tod_max=time_max,
                                   sunelev_min=sunelev_min,
                                   brt_min=brt_min,
                                   brt_max=brt_max)

    # check that some rows passed selection criteria
    nrows = len(roits_rows)
    if nrows == 0:
        print("No rows passed the selection criteria")
        return

    if verbose:
        print('Number of selected rows: {0}'.format(nrows))

    # make a list of dates for selected images
    img_date = []
    for row in roits_rows:
        img_date.append(row['datetime'].date())

    # list is ordered so find first and last dates
    dt_first = img_date[0]
    dt_last = img_date[nrows - 1]

    # set up a generator which yields dates for the start
    # of the next nday period covering the date range of image
    gcc_dr = daterange2(dt_first, dt_last, ndays)

    # calculate offset for timeseries based on nday
    day_offset = ndays / 2
    date_offset = timedelta(days=day_offset)

    # roits_ndx will be index into ROI timeseries
    roits_ndx = 0

    # set up vars for accumulating stats
    img_cnt = 0
    filenames = []
    r_dn_vals = []
    rcc_vals = []
    g_dn_vals = []
    gcc_vals = []
    b_dn_vals = []
    bcc_vals = []
    solar_elev_vals = []
    midday_delta_vals = []

    # loop over nday time periods
    for gcc_ndx, start_date in enumerate(gcc_dr):

        end_date = start_date + timedelta(ndays)
        gcc_date = start_date + date_offset
        doy = gcc_date.timetuple().tm_yday
        midday_noon = datetime(gcc_date.year,
                               gcc_date.month,
                               gcc_date.day, 12, 0, 0)

        # get roits rows for this time period
        while (roits_ndx < nrows and
               img_date[roits_ndx] >= start_date and
               img_date[roits_ndx] < end_date):
            filenames.append(roits_rows[roits_ndx]['filename'])
            r_dn = roits_rows[roits_ndx]['r_mean']
            r_dn_vals.append(r_dn)
            g_dn = roits_rows[roits_ndx]['g_mean']
            g_dn_vals.append(g_dn)
            b_dn = roits_rows[roits_ndx]['b_mean']
            b_dn_vals.append(b_dn)
            dnsum = r_dn + g_dn + b_dn

            # NOTE: I'm recomputing gcc, rcc, bcc from DN values rather
            # than using value stored in all-image CSV
            if dnsum <= 0:
                rcc = np.nan
                bcc = np.nan
                gcc = np.nan
            else:
                img_cnt += 1
                rcc = r_dn / dnsum
                bcc = b_dn / dnsum
                gcc = roits_rows[roits_ndx]['gcc']

            solar_elev = roits_rows[roits_ndx]['solar_elev']

            # note that rcc_vals can include NaN's
            rcc_vals.append(rcc)
            gcc_vals.append(gcc)
            bcc_vals.append(bcc)
            solar_elev_vals.append(solar_elev)
            midday_td = roits_rows[roits_ndx]['datetime'] - midday_noon
            midday_td_secs = np.abs(midday_td.days * 86400 + midday_td.seconds)
            midday_delta_vals.append(midday_td_secs)

            if roits_ndx < nrows:
                roits_ndx += 1
            else:
                break

        # check to see if we got any (good) images
        if img_cnt == 0:
            # nodata for this time period
            image_count = 0
            midday_filename = ND_STRING
            midday_r = ND_FLOAT
            midday_g = ND_FLOAT
            midday_b = ND_FLOAT
            midday_gcc = ND_FLOAT
            midday_rcc = ND_FLOAT
            r_mean = ND_FLOAT
            r_std = ND_FLOAT
            g_mean = ND_FLOAT
            g_std = ND_FLOAT
            b_mean = ND_FLOAT
            b_std = ND_FLOAT
            gcc_mean = ND_FLOAT
            gcc_std = ND_FLOAT
            gcc_50 = ND_FLOAT
            gcc_75 = ND_FLOAT
            gcc_90 = ND_FLOAT
            rcc_mean = ND_FLOAT
            rcc_std = ND_FLOAT
            rcc_50 = ND_FLOAT
            rcc_75 = ND_FLOAT
            rcc_90 = ND_FLOAT
            max_solar_elev = ND_FLOAT
            snow_flag = ND_INT
            outlierflag_gcc_mean = ND_INT
            outlierflag_gcc_50 = ND_INT
            outlierflag_gcc_75 = ND_INT
            outlierflag_gcc_90 = ND_INT

        # got some good images but not enough - probably there
        # are cases where this will fail e.g. not images on the
        # midday of a 3-day aggregation period.
        elif img_cnt < nimage_threshold:
            # not enough images
            image_count = img_cnt
            # find nearest image to midday (noon) on mid-interval date
            mi_ndx = midday_delta_vals.index(min(midday_delta_vals))
            midday_filename = filenames[mi_ndx]
            midday_r = r_dn_vals[mi_ndx]
            midday_g = g_dn_vals[mi_ndx]
            midday_b = b_dn_vals[mi_ndx]
            midday_gcc = gcc_vals[mi_ndx]
            midday_rcc = rcc_vals[mi_ndx]

            # no stats for this time interval
            r_mean = ND_FLOAT
            r_std = ND_FLOAT
            g_mean = ND_FLOAT
            g_std = ND_FLOAT
            b_mean = ND_FLOAT
            b_std = ND_FLOAT
            gcc_mean = ND_FLOAT
            gcc_std = ND_FLOAT
            gcc_50 = ND_FLOAT
            gcc_75 = ND_FLOAT
            gcc_90 = ND_FLOAT
            rcc_mean = ND_FLOAT
            rcc_std = ND_FLOAT
            rcc_50 = ND_FLOAT
            rcc_75 = ND_FLOAT
            rcc_90 = ND_FLOAT
            max_solar_elev = max(solar_elev_vals)
            snow_flag = ND_INT
            outlierflag_gcc_mean = ND_INT
            outlierflag_gcc_50 = ND_INT
            outlierflag_gcc_75 = ND_INT
            outlierflag_gcc_90 = ND_INT

        # stats for this period should be complete - only
        # snow flags are missing data
        else:
            # find nearest image to midday (noon) on mid-interval date
            mi_ndx = midday_delta_vals.index(min(midday_delta_vals))
            midday_filename = filenames[mi_ndx]
            midday_r = r_dn_vals[mi_ndx]
            midday_g = g_dn_vals[mi_ndx]
            midday_b = b_dn_vals[mi_ndx]
            midday_gcc = gcc_vals[mi_ndx]
            midday_rcc = rcc_vals[mi_ndx]

            # get stats for this time interval
            image_count = img_cnt
            r_mean = np.nanmean(r_dn_vals)
            r_std = np.nanstd(r_dn_vals)
            g_mean = np.nanmean(g_dn_vals)
            g_std = np.nanstd(g_dn_vals)
            b_mean = np.nanmean(b_dn_vals)
            b_std = np.nanstd(b_dn_vals)
            gcc_mean = np.nanmean(gcc_vals)
            gcc_std = np.nanstd(gcc_vals)
            gcc_50 = quantile(gcc_vals, .5)
            gcc_75 = quantile(gcc_vals, .75)
            gcc_90 = quantile(gcc_vals, .9)
            rcc_mean = np.nanmean(rcc_vals)
            rcc_std = np.nanstd(rcc_vals)
            rcc_50 = quantile(rcc_vals, .5)
            rcc_75 = quantile(rcc_vals, .75)
            rcc_90 = quantile(rcc_vals, .9)
            max_solar_elev = max(solar_elev_vals)
            snow_flag = ND_INT
            outlierflag_gcc_mean = ND_INT
            outlierflag_gcc_50 = ND_INT
            outlierflag_gcc_75 = ND_INT
            outlierflag_gcc_90 = ND_INT

        # append to gcc timeseries
        gcc_ts_row = gcc_ts.insert_row(gcc_date, doy, image_count,
                                       midday_filename,
                                       midday_r,
                                       midday_g,
                                       midday_b,
                                       midday_gcc,
                                       midday_rcc,
                                       r_mean, r_std,
                                       g_mean, g_std,
                                       b_mean, b_std,
                                       gcc_mean, gcc_std,
                                       gcc_50, gcc_75, gcc_90,
                                       rcc_mean, rcc_std,
                                       rcc_50, rcc_75, rcc_90,
                                       max_solar_elev, snow_flag,
                                       outlierflag_gcc_mean,
                                       outlierflag_gcc_50,
                                       outlierflag_gcc_75,
                                       outlierflag_gcc_90)

        # print(result if verbose)
        if verbose:
            csvstr = gcc_ts.format_csvrow(gcc_ts_row)
            print(csvstr)

        # reset accumulated values
        img_cnt = 0
        filenames = []
        r_dn_vals = []
        rcc_vals = []
        g_dn_vals = []
        gcc_vals = []
        b_dn_vals = []
        bcc_vals = []
        solar_elev_vals = []
        midday_delta_vals = []

    if dryrun:
        nout = 0
    else:
        nout = gcc_ts.writeCSV(outpath)

    print('Total: %d' % (nout,))


# run main when called from command line
if __name__ == "__main__":
    main()
