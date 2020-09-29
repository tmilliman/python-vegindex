#!/usr/bin/env python

"""
Update an ROI IR timeseries CSV file.
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import sys
from datetime import timedelta

# try python3 import then python2 import
try:
    from configparser import ConfigParser as configparser
except ImportError:
    from ConfigParser import SafeConfigParser as configparser

# use this because numpy/openblas is automatically multi-threaded.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np
from PIL import Image

import vegindex as vi
from vegindex.ir_roitimeseries import IRROITimeSeries
from vegindex.vegindex import get_roi_list

from . import utils

# use this because numpy/openblas is automatically multi-threaded.
os.environ["OMP_NUM_THREADS"] = "1"

# set vars

# you can set the archive directory to somewhere else for testing by
# using the env variable, PHENOCAM_ARCHIVE_DIR.
archive_dir = vi.config.archive_dir

debug = False
default_resize = vi.config.RESIZE


# if __name__ == "__main__":


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

    # positional arguments
    parser.add_argument("site", help="PhenoCam site name")
    parser.add_argument("roiname", help="ROI name, e.g. canopy_0001")

    # get args
    args = parser.parse_args()
    sitename = args.site
    roiname = args.roiname
    verbose = args.verbose
    dryrun = args.dry_run

    if verbose:
        print("site: {0}".format(sitename))
        print("roiname: {0}".format(roiname))
        print("verbose: {0}".format(verbose))
        print("dryrun: {0}".format(dryrun))

    # set input/output filename
    inname = "%s_%s_IR_roistats.csv" % (sitename, roiname)
    outname = inname
    inpath = os.path.join(archive_dir, sitename, "ROI", outname)
    outpath = inpath
    if verbose:
        print("output file: {0}".format(outname))

    # get ROI list
    roi_list = get_roi_list(sitename, roiname)

    # read existing CSV file - since this is an update throw
    # exception if the file doesn't already exist
    try:
        roits = IRROITimeSeries(site=sitename, ROIListID=roiname)
        roits.readCSV(inpath)
    except IOError:
        errmsg = "Unable to read IR CSV file: {0}\n".format(outpath)
        sys.stderr.write(errmsg)
        sys.exit(1)

    # read in config file for this site if it exists
    config_file = "{0}_{1}.cfg".format(sitename, roiname)
    config_path = os.path.join(archive_dir, sitename, "ROI", config_file)
    if os.path.exists(config_path):
        cfgparser = configparser(defaults={"resize": str(default_resize)})
        cfgparser.read(config_path)
        if cfgparser.has_section("roi_timeseries"):
            resizeFlg = cfgparser.getboolean("roi_timeseries", "resize")
        else:
            resizeFlg = default_resize

        # verify that config matches CSV header!
        if resizeFlg != roits.resizeFlg:
            errmsg = "resize flag from config doesn't match CSV header\n"
            sys.stderr.write(errmsg)
            sys.exit(1)

    else:
        resizeFlg = default_resize

    # print config values
    if verbose:
        print("")
        print("ROI timeseries config:")
        print("======================")
        print("roi_list: ", "{0}_{1}_roi.csv".format(sitename, roiname))
        if os.path.exists(config_path):
            print("config file: {0}".format(config_file))
        else:
            print("config file: None")
        print("Resize Flag: ", resizeFlg)

    # get list of images already in CSV
    old_imglist = roits.get_image_list()

    # find last dt in current timeseries CSV
    nlast = len(roits.rows) - 1
    dt_last = roits.rows[nlast]["datetime"]

    # add five seconds so that we don't reprocess last image
    dt_last = dt_last + timedelta(seconds=5)

    # start with images newer than last dt
    dt_start = dt_last

    if verbose:
        print("last image at: {0}".format(dt_last))

    # loop over mask entries in ROI list
    nimage = 0
    nupdate = 0
    for imask, roimask in enumerate(roi_list.masks):

        roi_startDT = roimask["start_dt"]
        roi_endDT = roimask["end_dt"]

        # skip this ROI maskfile if it's validity interval ends
        # before last date before update
        if roi_endDT < dt_start:
            continue

        # start_date = roi_startDT.date()
        # end_date = roi_endDT.date()
        # start_time = roi_startDT.time()
        # end_time = roi_endDT.time()
        maskfile = roimask["maskfile"]

        # okay set the start datetime to the larger of dt_start (from
        # last row of existing timeseries CSV) and the beginning of
        # the ROI validity.  We need to do this for the case where
        # there is a gap between last row of CSV and beginning of next
        # validity interval.  This will often be the case when there
        # are a series of "transitional images" between two
        # stable/useful camera positions.
        if dt_start < roi_startDT:
            dt_start = roi_startDT

        mask_path = os.path.join(archive_dir, sitename, "ROI", maskfile)
        # print roi_path
        try:
            mask_img = Image.open(mask_path)
        except Exception:
            sys.stderr.write("Unable to open ROI mask file\n")
            sys.exit(1)

        # check that mask_img is in expected form
        mask_mode = mask_img.mode
        if mask_mode != "L":

            # convert to 8-bit mask
            mask_img = mask_img.convert("L")

        # make a numpy mask
        roimask = np.asarray(mask_img, dtype=np.bool8)

        # get list of images for this timeperiod
        imglist = utils.getsiteimglist(
            sitename, getIR=True, startDT=dt_start, endDT=roi_endDT
        )

        nimage += len(imglist)
        for impath in imglist:

            if debug:
                print(maskfile, impath)

            # check if image already exists in list -- just to be
            # sure!
            fn = os.path.basename(impath)
            try:
                row_index = old_imglist.index(fn)
            except Exception:
                row_index = None

            # append/insert row for this image/mask - shouldn't happen
            # but just to be on safe side!
            if row_index:
                roits_row = roits.insert_row(impath, roimask, imask + 1)
            else:
                roits_row = roits.append_row(impath, roimask, imask + 1)

            # check that we could append/insert a row
            if roits_row:
                nupdate += 1
            else:
                continue

            if verbose:
                csvstr = roits.format_csvrow(roits_row)
                print(csvstr)

            if debug:
                if nupdate == 10:
                    break

    # output CSV file
    if dryrun:
        nout = 0
    else:
        nout = roits.writeCSV(outpath)

    print("Images processed: %d" % (nimage,))
    print("Images added to CSV: %d" % (nupdate,))
    print("Total: %d" % (nout,))
