#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command line script to make a simple PDF plot of gcc vs datetime using
the roistats file for a particular site and ROI.

"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd

# import vegindex as vi
from . import config

plt.style.use('ggplot')
archive_dir = config.archive_dir
MIN_SUN_ANGLE = config.MIN_SUN_ANGLE
MAX_BRT = config.MAX_BRT
MIN_BRT = config.MIN_BRT


def main():
    """
    Use pandas to generate plot of gcc values from roistats file.
    """

    # set up command line argument processing
    parser = argparse.ArgumentParser()

    # options
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
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

    if verbose:
        print("site: {0}".format(sitename))
        print("roiname: {0}".format(roiname))
        print("verbose: {0}".format(verbose))

    # set roistats input filename
    inname = "{}_{}_roistats.csv".format(sitename, roiname)
    indir = os.path.join(archive_dir, sitename, 'ROI')
    inpath = os.path.join(indir, inname)

    # set 3-day summary input filename
    inname2 = "{}_{}_3day.csv".format(sitename, roiname)
    inpath2 = os.path.join(indir, inname2)

    # set output filename
    outname = "{}_{}_roistats.pdf".format(sitename, roiname)
    outdir = os.path.join(archive_dir, sitename, 'ROI')
    outpath = os.path.join(outdir, outname)

    if verbose:
        print("archive dir: {}".format(archive_dir))
        print("ROI dir: {}".format(outdir))
        print("ROI stats file: {}".format(inname))
        print("3-day summary file: {}".format(inname2))
        print("output file: {}".format(outname))

    # read in roistats CSV file
    df = pd.read_csv(inpath, comment="#", parse_dates=[[0, 1]])

    # index data frame by datetime
    df.index = df.date_local_std_time

    # add a column for ROI brightness (r_mean + g_mean + b_mean)
    df['brt'] = df['r_mean'] + df['g_mean'] + df['b_mean']

    # for the gcc percentiles we filter data first
    #
    # NOTE: should use vegindex routines to read the ROI list
    # which should pick up any overrides of the defaults!
    #
    df_low = df[df.solar_elev < MIN_SUN_ANGLE]
    df_day = df[df.solar_elev >= MIN_SUN_ANGLE]
    df_brt_filtered = df_day[(df_day.brt < MIN_BRT) |
                             (df_day.brt > MAX_BRT)]
    df_good = df_day[(df_day.brt >= MIN_BRT) & (df_day.brt <= MAX_BRT)]
    df_filtered = pd.concat([df_low, df_brt_filtered])
    nrows_filtered, ncols = df_filtered.shape

    # read in 3-day summary filename
    df2 = pd.read_csv(inpath2, comment="#", parse_dates=[0])
    df2.index = df2.date

    # make plot
    ax = df_good.gcc.plot(style='k.', markersize=.3, figsize=[16, 5])
    if nrows_filtered > 0:
        df_filtered.gcc.plot(style='r.', ax=ax, markersize=.5)
    df2.gcc_90.plot(style='g-', ax=ax)

    ax.set_title('{} {}'.format(sitename, roiname))
    ax.set_ylabel('gcc')
    ax.set_xlabel('date')
    lines, labels = ax.get_legend_handles_labels()
    if nrows_filtered > 0:
        ax.legend(lines[1:], ['filtered values',
                              '3-day gcc 90th percentile'],
                  loc="best")
    else:
        ax.legend(lines[1:], ['3-day gcc 90th percentile'],
                  loc="best")

    fig = ax.get_figure()
    fig.savefig(outpath)


if __name__ == "__main__":
    main()
