# -*- coding: utf-8 -*-

"""
Update summary time series CSV file.
"""

import argparse
import os
import sys
from configparser import ConfigParser
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

# use this because numpy/openblas is automatically multi-threaded.
os.environ["OMP_NUM_THREADS"] = "1"
import numpy as np

from vegindex import vegindex as vi

from .quantile import quantile

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

# default image selectors
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
        help="Number of Days to Aggregate",
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

    # set up output filename
    outdir = os.path.join(vi.config.archive_dir, sitename, "ROI")
    outfile = "{0}_{1}_{2}day.csv".format(sitename, roiname, ndays)
    outpath = os.path.join(outdir, outfile)

    # since this is "update" output file should already exist
    # if not just bail out
    if not os.path.exists(outpath):
        sys.stderr.write("Existing gcc90 file {0} not found.\n".format(outpath))
        sys.exit(1)

    # read in existing CSV file
    gcc_ts = vi.GCCTimeSeries(site=sitename, ROIListID=roiname, nday=ndays)
    gcc_ts.readCSV(outpath)

    # read in config file for this site/roi if it exists
    config_file = "{0}_{1}.cfg".format(sitename, roiname)
    config_path = os.path.join(archive_dir, sitename, "ROI", config_file)
    if os.path.exists(config_path):
        cfgparser = ConfigParser(
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
            print("time_max_str: {0}".format(time_max_str))
            [tmax_hr, tmax_mn, tmax_sc] = time_max_str.split(":")
            time_max = time(int(tmax_hr), int(tmax_mn), int(tmax_sc))
            time_min_str = cfgparser.get("gcc90_calculation", "time_min")
            [tmin_hr, tmin_mn, tmin_sc] = time_min_str.split(":")
            time_min = time(int(tmin_hr), int(tmin_mn), int(tmin_sc))
            sunelev_min = cfgparser.getfloat("gcc90_calculation", "sunelev_min")
            brt_min = cfgparser.getint("gcc90_calculation", "brt_min")
            brt_max = cfgparser.getint("gcc90_calculation", "brt_max")
        else:
            nimage_threshold = gcc_ts.nmin
            time_max = gcc_ts.tod_max
            time_min = gcc_ts.tod_min
            sunelev_min = gcc_ts.sunelev_min
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

    # verify that config file matches CSV header!
    if nimage_threshold != gcc_ts.nmin:
        sys.stderr.write("nimage_threshold from config doesn't match CSV header\n")
        sys.exit(1)
    if brt_min != gcc_ts.brt_min:
        sys.stderr.write("brt_min from config file doesn't match CSV header\n")
        sys.exit(1)
    if brt_max != gcc_ts.brt_max:
        sys.stderr.write("brt_max from config file doesn't match CSV header\n")
        sys.exit(1)
    if time_min != gcc_ts.tod_min:
        sys.stderr.write("tod_min from config file doesn't match CSV header\n")
        sys.exit(1)
    if time_min != gcc_ts.tod_min:
        sys.stderr.write("tod_min from config file doesn't match CSV header\n")
        sys.exit(1)
    if sunelev_min != gcc_ts.sunelev_min:
        sys.stderr.write("sunelev_min from config file doesn't match CSV header\n")
        sys.exit(1)

    else:

        nimage_threshold = gcc_ts.nmin
        time_max = gcc_ts.tod_max
        time_min = gcc_ts.tod_min
        sunelev_min = gcc_ts.sunelev_min
        brt_min = default_brt_min
        brt_max = default_brt_max

    # grab remaining metadata
    gcc_ts_create_date = gcc_ts.created_at
    gcc_ts_update_date = gcc_ts.updated_at

    # print config values
    if verbose:
        print("")
        print("gcc config:")
        print("===========")
        print("roi_list: ", "{0}_{1}".format(sitename, roiname))
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
        print("creation date: ", gcc_ts_create_date)
        print("last update: ", gcc_ts_update_date)

    # get number of rows in existing/old CSV
    ngccrows = len(gcc_ts.rows)

    # get the next to last date in gcc90 CSV
    # NOTE: always redo last date since we may be adding images
    # (if ndays > 1 and we haven't finished interval)
    gcc90_date_last = gcc_ts.rows[ngccrows - 1]["date"]

    if verbose:
        print("last date in timeseries: ", gcc90_date_last)
        print("")

    # get roi timeseries for this site and roi
    roits = vi.get_roi_timeseries(sitename, roiname)

    if verbose:
        print("")
        print("ROI timeseries info:")
        print("====================")
        print("site: ", roits.site)
        print("ROI list id: ", roits.roilistid)
        print("create date: ", roits.created_at)
        print("update date: ", roits.updated_at)
        print("nrows: ", len(roits.rows))

    # make list of rows which match image selection criteria
    roits_rows = roits.select_rows(
        tod_min=time_min,
        tod_max=time_max,
        sunelev_min=sunelev_min,
        brt_min=brt_min,
        brt_max=brt_max,
    )

    # calculate offset for timeseries based on nday
    day_offset = ndays / 2
    date_offset = timedelta(days=day_offset)

    # find rows that are in or more recent than beginning of last timeperiod
    # of GCC
    new_roits_rows = []
    for row in roits_rows:

        if row["datetime"].date() >= (gcc90_date_last - date_offset):
            new_roits_rows.append(row)

    # check that some rows passed selection criteria
    nrows = len(new_roits_rows)
    if nrows == 0:
        print("No rows passed the selection criteria")
        sys.exit(0)

    if debug:
        print("New selected rows: {0}".format(nrows))

    # make a list of dates for selected images
    img_date = []
    for row in new_roits_rows:
        img_date.append(row["datetime"].date())

    # list is ordered so find first and last dates
    dt_first = img_date[0]
    dt_last = img_date[nrows - 1]

    # set up a generator which yields dates for the start
    # of the next nday period covering the date range of
    # new images
    gcc_dr = vi.daterange2(dt_first, dt_last, ndays)

    # roits_ndx will be index into ROI timeseries
    roits_ndx = 0

    # set up vars for accumulating stats
    img_cnt = 0
    update_cnt = 0
    filenames = []
    r_dn_vals = []
    rcc_vals = []
    g_dn_vals = []
    gcc_vals = []
    b_dn_vals = []
    bcc_vals = []
    solar_elev_vals = []
    midday_delta_vals = []

    # loop over ndays time periods
    for gcc_ndx, start_date in enumerate(gcc_dr):

        end_date = start_date + timedelta(ndays)
        gcc_date = start_date + date_offset
        doy = gcc_date.timetuple().tm_yday
        midday_noon = datetime(gcc_date.year, gcc_date.month, gcc_date.day, 12, 0, 0)

        # get roits rows for this time period
        while (
            roits_ndx < nrows
            and img_date[roits_ndx] >= start_date
            and img_date[roits_ndx] < end_date
        ):
            filenames.append(new_roits_rows[roits_ndx]["filename"])
            r_dn = new_roits_rows[roits_ndx]["r_mean"]
            r_dn_vals.append(r_dn)
            g_dn = new_roits_rows[roits_ndx]["g_mean"]
            g_dn_vals.append(g_dn)
            b_dn = new_roits_rows[roits_ndx]["b_mean"]
            b_dn_vals.append(b_dn)
            dnsum = r_dn + g_dn + b_dn
            if dnsum <= 0:
                rcc = np.nan
                bcc = np.nan
                gcc = np.nan
            else:
                rcc = r_dn / dnsum
                bcc = b_dn / dnsum
                gcc = new_roits_rows[roits_ndx]["gcc"]

            solar_elev = new_roits_rows[roits_ndx]["solar_elev"]
            rcc_vals.append(rcc)
            gcc_vals.append(gcc)
            bcc_vals.append(bcc)
            solar_elev_vals.append(solar_elev)
            midday_td = new_roits_rows[roits_ndx]["datetime"] - midday_noon
            midday_td_secs = np.abs(midday_td.days * 86400 + midday_td.seconds)
            midday_delta_vals.append(midday_td_secs)
            img_cnt += 1

            if roits_ndx < nrows:
                roits_ndx += 1
            else:
                break

        # check to see if we got any images
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

        elif img_cnt < nimage_threshold:
            # not enough images
            image_count = img_cnt
            # find nearest image to midday (noon) on mid-interval date
            mi_ndx = midday_delta_vals.index(min(midday_delta_vals))
            midday_filename = filenames[mi_ndx]
            if not midday_filename:
                midday_filename = ND_STRING
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
            gcc_50 = quantile(gcc_vals, 0.5)
            gcc_75 = quantile(gcc_vals, 0.75)
            gcc_90 = quantile(gcc_vals, 0.9)
            rcc_mean = np.mean(rcc_vals)
            rcc_std = np.std(rcc_vals)
            rcc_50 = quantile(rcc_vals, 0.5)
            rcc_75 = quantile(rcc_vals, 0.75)
            rcc_90 = quantile(rcc_vals, 0.9)
            max_solar_elev = max(solar_elev_vals)
            snow_flag = ND_INT
            outlierflag_gcc_mean = ND_INT
            outlierflag_gcc_50 = ND_INT
            outlierflag_gcc_75 = ND_INT
            outlierflag_gcc_90 = ND_INT

        # append to gcc timeseries
        gcc_ts_row = gcc_ts.insert_row(
            gcc_date,
            doy,
            image_count,
            midday_filename,
            midday_r,
            midday_g,
            midday_b,
            midday_gcc,
            midday_rcc,
            r_mean,
            r_std,
            g_mean,
            g_std,
            b_mean,
            b_std,
            gcc_mean,
            gcc_std,
            gcc_50,
            gcc_75,
            gcc_90,
            rcc_mean,
            rcc_std,
            rcc_50,
            rcc_75,
            rcc_90,
            max_solar_elev,
            snow_flag,
            outlierflag_gcc_mean,
            outlierflag_gcc_50,
            outlierflag_gcc_75,
            outlierflag_gcc_90,
        )

        update_cnt += 1

        # print result if verbose
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

    print("GCC90 Rows updated: 1  Rows added: {0}".format(update_cnt - 1))
    print("Total: {0}".format(nout))


# run main when called from command line
if __name__ == "__main__":
    main()
