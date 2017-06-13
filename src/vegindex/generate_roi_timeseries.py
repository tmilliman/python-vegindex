# -*- coding: utf-8 -*-

"""
Command line script to generate a ROI timeseries CSV from images for a
particular site and ROI.  All available images will be include.

"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import sys

import numpy as np
from PIL import Image

import vegindex as vi
from vegindex.roitimeseries import ROITimeSeries
from vegindex.vegindex import get_roi_list

from . import utils

# try python3 import then python2 import
try:
    import configparser
except:
    from ConfigParser import SafeConfigParser as configparser

# set vars

# you can set the archive directory to somewhere else for testing by
# using the env variable, PHENOCAM_ARCHIVE_DIR.
archive_dir = vi.config.archive_dir

debug = False
default_resize = vi.config.RESIZE


# if __name__ == "__main__":
def main():
    """
    generate ROI timeseries from a PhenoCam directory of images
    """

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

    # positional arguments
    parser.add_argument("site", help="PhenoCam site name")
    parser.add_argument("roiname", help="ROI name, e.g. DB_0001")

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

    # set output filename
    outname = '%s_%s_timeseries.csv' % (sitename, roiname,)
    outdir = os.path.join(archive_dir, sitename, 'ROI')
    outpath = os.path.join(outdir, outname)
    if verbose:
        print("archive dir: {0}".format(archive_dir))
        print("output file: {0}".format(outname))

    # read in config file for this site if it exists
    config_file = "{0}_{1}.cfg".format(sitename, roiname)
    config_path = os.path.join(archive_dir, sitename, 'ROI',
                               config_file)
    if os.path.exists(config_path):
        cfgparser = configparser(
            defaults={'resize': str(default_resize)})
        cfgparser.read(config_path)
        if cfgparser.has_section('roi_timeseries'):
            resizeFlg = cfgparser.getboolean('roi_timeseries', 'resize')
        else:
            resizeFlg = default_resize

    else:
        resizeFlg = default_resize

    # print config values
    if verbose:
        print('')
        print('ROI timeseries config:')
        print('======================')
        print('roi_list: ', '{0}_{1}_roi.csv'.format(sitename, roiname))
        if os.path.exists(config_path):
            print("config file: {0}".format(config_file))
        else:
            print("config file: None")
        print('Resize Flag: ', resizeFlg)

    # create new roi_timeseries object for this ROIList
    roits = ROITimeSeries(site=sitename, ROIListID=roiname,
                          resizeFlag=resizeFlg)

    # grab roi list
    roi_list = get_roi_list(sitename, roiname)

    # loop over mask entries in ROI list
    nimage = 0
    nupdate = 0
    for roimask_index, roimask in enumerate(roi_list.masks):

        startDT = roimask['start_dt']
        endDT = roimask['end_dt']
        maskfile = roimask['maskfile']

        mask_path = os.path.join(archive_dir, sitename, 'ROI', maskfile)
        # open roi mask file
        try:
            mask_img = Image.open(mask_path)

        except:
            sys.stderr.write("Unable to open ROI mask file\n")
            sys.exit(1)

        # check that mask_img is in expected form
        mask_mode = mask_img.mode
        if mask_mode != 'L':

            # convert to 8-bit mask
            mask_img = mask_img.convert('L')

        # make a numpy mask
        roimask = np.asarray(mask_img, dtype=np.bool8)

        # get list of images for this timeperiod
        imglist = utils.getsiteimglist(sitename, getIR=False,
                                       startDT=startDT, endDT=endDT)

        nimage += len(imglist)

        for impath in imglist:

            # append row for this image/mask - shouldn't get
            # any duplicates so just append
            roits_row = roits.append_row(impath, roimask,
                                         roimask_index + 1)
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

    print('Images processed: %d' % (nimage,))
    print('Images added to CSV: %d' % (nupdate,))
    print('Total: %d' % (nout,))


if __name__ == '__main__':
    main()
