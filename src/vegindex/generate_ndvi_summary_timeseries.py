#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to generate a csv with summary files from a roi NDVI
timeseries csv file.  Output format will be:

<TBD>
date,year,doy,image_count,midday_rgb_filename,midday_ir_filename,
midday_ndvi,gcc_90,ndvi_mean,ndvi_std,ndvi_50,ndvi_75,ndvi_90,
max_solar_elev,snow_flag,outlierflag_ndvi_50,outlierflag_ndvi_75,
outlierflag_ndvi_90
<TBD>

The following image selection parameters are read from a config file
(if it's present) or set to a default if not.  Only values changed
from defaults need to be in the config file.

default_nimage_threshold=1
default_time_min='00:00:00'
default_time_max='23:59:59'

Here's a sample config file which should be named
<sitename>_<roi-id>.cfg and be in the ROI directory
of the data archive for the site.  We use the same
parameters as for the gcc90 calculation:

----start of gcc90_calculation section----
[gcc90_calculation]
nimage_threshold=5

----end of file----

You can specify any of the above parameters to configure
image selection in the calculations.

"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import sys
from datetime import datetime
from datetime import time
from datetime import timedelta

try:
    import configparser
except ImportError:
    from ConfigParser import SafeConfigParser as configparser

import numpy as np

import vegindex as vi
from vegindex.ndvi_summary_timeseries import NDVISummaryTimeSeries
from vegindex.ndvitimeseries import NDVITimeSeries
from vegindex.quantile import quantile
from vegindex.vegindex import daterange2
from vegindex.vegindex import get_ndvi_timeseries

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
    parser = argparse.ArgumentParser(
        description="Generate a summary/aggregated NDVI file"
    )

    # options
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        help="Process data but don't save results",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--aggregation-period",
        help="Number of Days to Aggregate (default=1)",
        nargs="?",
        type=int,
        choices=range(1, 5, 2),
        default=1,
    )

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
    config_path = os.path.join(archive_dir, sitename, "ROI", config_file)
    if os.path.exists(config_path):
        # NOTE: should probably subclass safe config parser
        # and add gettime() method which checks for time validity
        cfgparser = configparser(
            defaults={
                "nimage_threshold": str(default_nimage_threshold),
                "time_min": str(default_time_min),
                "time_max": str(default_time_max),
                "sunelev_min": str(default_sunelev_min),
                "brt_min": str(default_brt_min),
                "brt_max": str(default_brt_max),
            }
        )

        cfgparser.read(config_path)

        if cfgparser.has_section("gcc90_calculation"):
            nimage_threshold = cfgparser.getint("gcc90_calculation", "nimage_threshold")
            time_max_str = cfgparser.get("gcc90_calculation", "time_max")
            [tmax_hr, tmax_mn, tmax_sc] = time_max_str.split(":")
            time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
            time_min_str = cfgparser.get("gcc90_calculation", "time_min")
            [tmin_hr, tmin_mn, tmin_sc] = time_min_str.split(":")
            time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
            sunelev_min = cfgparser.getfloat("gcc90_calculation", "sunelev_min")
            brt_min = cfgparser.getint("gcc90_calculation", "brt_min")
            brt_max = cfgparser.getint("gcc90_calculation", "brt_max")
        else:
            nimage_threshold = int(default_nimage_threshold)
            [tmax_hr, tmax_mn, tmax_sc] = default_time_max.split(":")
            time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
            [tmin_hr, tmin_mn, tmin_sc] = default_time_min.split(":")
            time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
            sunelev_min = default_sunelev_min
            brt_min = default_brt_min
            brt_max = default_brt_max

    else:
        nimage_threshold = int(default_nimage_threshold)
        [tmax_hr, tmax_mn, tmax_sc] = default_time_max.split(":")
        time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
        [tmin_hr, tmin_mn, tmin_sc] = default_time_min.split(":")
        time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
        sunelev_min = default_sunelev_min
        brt_min = default_brt_min
        brt_max = default_brt_max

    # print config values
    if verbose:
        print("")
        print("gcc config:")
        print("===========")
        print("roi_list: ", "{0}_{1}_roi.csv".format(sitename, roiname))
        if os.path.exists(config_path):
            print("config file: {0}".format(config_file))
        else:
            print("config file: None")
        print("nimage threshold: ", nimage_threshold)
        print("time of day min: ", time_min)
        print("time of day max: ", time_max)
        print("sun elev min: ", sunelev_min)
        print("aggregate days: ", ndays)
        print("minimum brightness: ", brt_min)
        print("maximum brightness: ", brt_max)

    # set up output filename
    outdir = os.path.join(archive_dir, sitename, "ROI")
    outfile = "{0}_{1}_ndvi_{2}day.csv".format(sitename, roiname, ndays)
    outpath = os.path.join(outdir, outfile)
    if verbose:
        print("output file: ", outfile)

    # create NDVI Summary timeseries object as empty list
    ndvi_summary_ts = NDVISummaryTimeSeries(
        site=sitename,
        ROIListID=roiname,
        nday=ndays,
        nmin=nimage_threshold,
        tod_min=time_min,
        tod_max=time_max,
        sunelev_min=sunelev_min,
        brt_min=brt_min,
        brt_max=brt_max,
    )

    # get NDVI timeseries for this site and roi
    ndvits = get_ndvi_timeseries(sitename, roiname)

    if verbose:
        print("")
        print("NDVI timeseries info:")
        print("=====================")
        print("site: ", ndvits.site)
        print("ROI list id: ", ndvits.roilistid)
        print("create date: ", ndvits.created_at)
        print("update date: ", ndvits.updated_at)
        print("nrows: ", len(ndvits.rows))

    # make list of rows which match image selection criteria
    ndvits_rows = ndvits.select_rows(
        tod_min=time_min,
        tod_max=time_max,
        sunelev_min=sunelev_min,
        brt_min=brt_min,
        brt_max=brt_max,
    )

    # check that some rows passed selection criteria
    nrows = len(ndvits_rows)
    if nrows == 0:
        print("No rows passed the selection criteria")
        return

    if verbose:
        print("Number of selected rows: {0}".format(nrows))

    # make a list of dates for selected images
    img_date = []
    for row in ndvits_rows:
        img_date.append(row["datetime"].date())

    # list is ordered so find first and last dates
    dt_first = img_date[0]
    dt_last = img_date[nrows - 1]

    # set up a generator which yields dates for the start
    # of the next nday period covering the date range of image
    ndvi_dr = daterange2(dt_first, dt_last, ndays)

    # calculate offset for timeseries based on nday
    day_offset = ndays / 2
    date_offset = timedelta(days=day_offset)

    # ndvits_ndx will be index into ROI timeseries
    ndvits_ndx = 0

    # loop over nday time periods
    for ndvi_ndx, start_date in enumerate(ndvi_dr):

        # set up vars for accumulating stats for this period
        img_cnt = 0
        rgb_filenames = []
        ir_filenames = []
        r_mean_vals = []
        g_mean_vals = []
        b_mean_vals = []
        ir_mean_vals = []
        gcc_vals = []
        ndvi_vals = []
        solar_elev_vals = []
        midday_delta_vals = []

        end_date = start_date + timedelta(ndays)
        ndvi_date = start_date + date_offset
        doy = ndvi_date.timetuple().tm_yday
        midday_noon = datetime(ndvi_date.year, ndvi_date.month, ndvi_date.day, 12, 0, 0)

        # get ndvits rows for this time period
        while (
            ndvits_ndx < nrows
            and img_date[ndvits_ndx] >= start_date
            and img_date[ndvits_ndx] < end_date
        ):

            # # skip this row if awbflag is 1
            # if ndvits_rows[ndvits_ndx]["awbflag"] == 1:
            #     if ndvits_ndx < nrows:
            #         ndvits_ndx += 1
            #         continue
            #     else:
            #         break

            # # filter on exposures
            # exposure_ir = ndvits_rows[ndvits_ndx]["exposure_ir"]
            # exposure_rgb = ndvits_rows[ndvits_ndx]["exposure_rgb"]

            # if exposure_ir/exposure_rgb > 0.8:
            #     ndvits_ndx += 1
            #     continue

            # # filter on negative NDVI
            # if ndvits_rows[ndvits_ndx]["NDVI_c"] < 0:
            #     ndvits_ndx += 1
            #     continue

            rgb_filenames.append(ndvits_rows[ndvits_ndx]["filename_rgb"])
            ir_filenames.append(ndvits_rows[ndvits_ndx]["filename_ir"])
            r_dn = ndvits_rows[ndvits_ndx]["r_mean"]
            r_mean_vals.append(r_dn)
            g_dn = ndvits_rows[ndvits_ndx]["g_mean"]
            g_mean_vals.append(g_dn)
            b_dn = ndvits_rows[ndvits_ndx]["b_mean"]
            b_mean_vals.append(b_dn)
            ir_dn = ndvits_rows[ndvits_ndx]["ir_mean"]
            ir_mean_vals.append(ir_dn)
            dnsum = r_dn + g_dn + b_dn

            # check that dnsum > 0 -- not sure why this is here!
            if dnsum <= 0:
                gcc = np.nan
            else:
                img_cnt += 1
                gcc = ndvits_rows[ndvits_ndx]["gcc"]
            gcc_vals.append(gcc)
            ndvi = ndvits_rows[ndvits_ndx]["NDVI_c"]
            ndvi_vals.append(ndvi)
            solar_elev = ndvits_rows[ndvits_ndx]["solar_elev"]
            solar_elev_vals.append(solar_elev)
            midday_td = ndvits_rows[ndvits_ndx]["datetime"] - midday_noon
            midday_td_secs = np.abs(midday_td.days * 86400 + midday_td.seconds)
            midday_delta_vals.append(midday_td_secs)

            if ndvits_ndx < nrows:
                ndvits_ndx += 1
            else:
                break

        # check to see if we got any (good) images
        if img_cnt == 0:
            # nodata for this time period
            image_count = 0
            midday_rgb_filename = ND_STRING
            midday_ir_filename = ND_STRING
            midday_ndvi = ND_FLOAT
            gcc_90 = ND_FLOAT
            ndvi_mean = ND_FLOAT
            ndvi_std = ND_FLOAT
            ndvi_50 = ND_FLOAT
            ndvi_75 = ND_FLOAT
            ndvi_90 = ND_FLOAT
            max_solar_elev = ND_FLOAT
            snow_flag = ND_INT
            outlierflag_ndvi_mean = ND_INT
            outlierflag_ndvi_50 = ND_INT
            outlierflag_ndvi_75 = ND_INT
            outlierflag_ndvi_90 = ND_INT

        # got some good images but not enough - probably there
        # are cases where this will fail e.g. no images on the
        # midday of a 3-day aggregation period.
        elif img_cnt < nimage_threshold:
            # not enough images
            image_count = img_cnt
            # find nearest image to midday (noon) on mid-interval date
            mi_ndx = midday_delta_vals.index(min(midday_delta_vals))
            midday_rgb_filename = rgb_filenames[mi_ndx]
            midday_ir_filename = ir_filenames[mi_ndx]
            midday_ndvi = ndvi_vals[mi_ndx]

            # no stats for this time interval
            gcc_90 = ND_FLOAT
            ndvi_mean = ND_FLOAT
            ndvi_std = ND_FLOAT
            ndvi_50 = ND_FLOAT
            ndvi_75 = ND_FLOAT
            ndvi_90 = ND_FLOAT
            max_solar_elev = max(solar_elev_vals)
            snow_flag = ND_INT
            outlierflag_ndvi_mean = ND_INT
            outlierflag_ndvi_50 = ND_INT
            outlierflag_ndvi_75 = ND_INT
            outlierflag_ndvi_90 = ND_INT

        # stats for this period should be complete - only
        # snow flags and outliers are missing data
        else:
            # find nearest image to midday (noon) on mid-interval date
            mi_ndx = midday_delta_vals.index(min(midday_delta_vals))
            midday_rgb_filename = rgb_filenames[mi_ndx]
            midday_ir_filename = ir_filenames[mi_ndx]
            midday_ndvi = ndvi_vals[mi_ndx]

            # get stats for this time interval
            image_count = img_cnt
            gcc_90 = quantile(gcc_vals, 0.9)
            ndvi_mean = np.nanmean(ndvi_vals)
            ndvi_std = np.nanstd(ndvi_vals)
            ndvi_50 = quantile(ndvi_vals, 0.5)
            ndvi_75 = quantile(ndvi_vals, 0.75)
            ndvi_90 = quantile(ndvi_vals, 0.9)
            max_solar_elev = max(solar_elev_vals)
            snow_flag = ND_INT
            outlierflag_ndvi_mean = ND_INT
            outlierflag_ndvi_50 = ND_INT
            outlierflag_ndvi_75 = ND_INT
            outlierflag_ndvi_90 = ND_INT

        # append to NDVI timeseries
        year = ndvi_date.year
        ndvi_ts_row = ndvi_summary_ts.insert_row(
            ndvi_date,
            year,
            doy,
            image_count,
            midday_rgb_filename,
            midday_ir_filename,
            midday_ndvi,
            gcc_90,
            ndvi_mean,
            ndvi_std,
            ndvi_50,
            ndvi_75,
            ndvi_90,
            max_solar_elev,
            snow_flag,
            outlierflag_ndvi_mean,
            outlierflag_ndvi_50,
            outlierflag_ndvi_75,
            outlierflag_ndvi_90,
        )

        # print(result if verbose)
        if verbose:
            csvstr = ndvi_summary_ts.format_csvrow(ndvi_ts_row)
            print(csvstr)

    if dryrun:
        nout = 0
    else:
        nout = ndvi_summary_ts.writeCSV(outpath)

    print("Total: %d" % (nout,))


# run main when called from command line
if __name__ == "__main__":
    main()
