#!/usr/bin/env python

"""
Simple script to read in the RGB and IR ROI timeseries and
generate a camera NDVI timeseries csv file.  Output
format will be:

"""

import argparse
import os
import sys
from datetime import datetime
from datetime import timedelta

import pandas as pd

# use this because numpy/openblas is automatically multi-threaded.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np

from vegindex import vegindex as vi
from vegindex.roitimeseries import ROITimeSeries

# set vars

# you can set the archive directory to somewhere else for testing by
# using the env variable, PHENOCAM_ARCHIVE_DIR.
archive_dir = vi.config.archive_dir

# set missing/no-data values
ND_FLOAT = vi.config.ND_FLOAT
ND_INT = vi.config.ND_INT
ND_STRING = vi.config.ND_STRING


def main():

    # set up command line argument processing
    parser = argparse.ArgumentParser(
        description="Merge RGB and IR stats and calculate camera NDVI"
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

    # construct name for roistats files
    indir = os.path.join(archive_dir, sitename, "ROI")
    rgb_file = "{}_{}_roistats.csv".format(sitename, roiname)
    ir_file = "{}_{}_IR_roistats.csv".format(sitename, roiname)

    # set up output filename
    outdir = os.path.join(archive_dir, sitename, "ROI")
    outfile = "{0}_{1}_ndvi.csv".format(sitename, roiname)
    outpath = os.path.join(outdir, outfile)

    if verbose:
        print("RGB roistats: ", rgb_file)
        print("IR roistats: ", ir_file)
        print("output file: ", outfile)

    rgb_path = os.path.join(indir, rgb_file)
    ir_path = os.path.join(indir, ir_file)

    # read in the RGB ROI stats file using the vegindex class
    # to get the header information

    # Since this is an update throw exception if the file doesn't
    # already exist
    try:
        roits = ROITimeSeries(site=sitename, ROIListID=roiname)
        roits.readCSV(rgb_path)
    except IOError:
        errmsg = "Unable to read CSV file: {0}\n".format(rgb_path)
        sys.stderr.write(errmsg)
        sys.exit(1)

    # use pandas to read in the RGB and IR CSV files into a data frame
    # Throw an exception if the file doesn't exist
    try:
        df_rgb = pd.read_csv(
            rgb_path, comment="#", parse_dates=[[0, 1]], na_values="NA"
        )
    except IOError:
        errmsg = "Unable to read RGB CSV file: {}\n".format(rgb_path)
        sys.stderr.write(errmsg)
        sys.exit(1)

    try:
        df_ir = pd.read_csv(ir_path, comment="#", parse_dates=[[0, 1]], na_values="NA")
    except IOError:
        errmsg = "Unable to read IR CSV file: {}\n".format(ir_path)
        sys.stderr.write(errmsg)
        sys.exit(1)

    # check the number of rows in each dataframe
    nrows_ir = len(df_ir)
    nrows_rgb = len(df_rgb)
    if verbose:
        print("IR rows: {}".format(nrows_ir))
        print("RGB rows: {}".format(nrows_rgb))

    # Merge the the two dataframes based on datetime.  For sites
    # which have been configured with the current PIT scripts the
    # times will match identically.  For older sites they will be
    # close but not exact.
    dt_tolerance = timedelta(minutes=10)
    df_combined = pd.merge_asof(
        df_rgb,
        df_ir,
        on="date_local_std_time",
        suffixes=("_rgb", "_ir"),
        direction="nearest",
        tolerance=dt_tolerance,
    )

    # eliminate rows where there is no matching IR filename
    df_combined = df_combined[df_combined.filename_ir.notnull()]
    len_combined = len(df_combined)
    if verbose:
        print("Matched rows: {}".format(len_combined))

    # eliminate rows where there is no RGB or IR exposure
    df_combined = df_combined[df_combined.exposure_ir.notnull()]
    df_combined = df_combined[df_combined.exposure_rgb.notnull()]

    # eliminate rows where either exposure is 0.  This is
    # an indication that the OCR of the exposure failed so maybe
    # letting this generate an error would be better.  The
    # resulting CSV would have "inf" or "-inf" in the output.
    df_combined = df_combined[df_combined.exposure_ir != 0]
    df_combined = df_combined[df_combined.exposure_rgb != 0]

    # eliminate rows where there is no DN values
    df_combined = df_combined[df_combined.r_mean.notnull()]
    df_combined = df_combined[df_combined.g_mean.notnull()]
    df_combined = df_combined[df_combined.b_mean.notnull()]
    df_combined = df_combined[df_combined.ir_mean.notnull()]

    # add some columns following Petach, et al.
    df_combined["Y"] = (
        0.3 * df_combined["r_mean"]
        + 0.59 * df_combined["g_mean"]
        + 0.11 * df_combined["b_mean"]
    )

    df_combined["Z_prime"] = df_combined["ir_mean"] / np.sqrt(
        df_combined["exposure_ir"]
    )
    df_combined["R_prime"] = df_combined["r_mean"] / np.sqrt(
        df_combined["exposure_rgb"]
    )
    df_combined["Y_prime"] = df_combined["Y"] / np.sqrt(df_combined["exposure_rgb"])
    df_combined["X_prime"] = df_combined["Z_prime"] - df_combined["Y_prime"]
    df_combined["NDVI_c"] = (df_combined["X_prime"] - df_combined["R_prime"]) / (
        df_combined["X_prime"] + df_combined["R_prime"]
    )

    # add separate columns for date and local_std_time
    df_combined["date"] = df_combined["date_local_std_time"].dt.date
    df_combined["local_std_time"] = df_combined["date_local_std_time"].dt.time

    # convert some columns to integers
    df_combined = df_combined.astype(
        {
            "doy_rgb": "int32",
            "exposure_rgb": "int32",
            "exposure_ir": "int32",
            "mask_index_rgb": "int32",
            "r_mean": "int32",
            "g_mean": "int32",
            "b_mean": "int32",
            "ir_mean": "int32",
        }
    )
    # remove some columns
    df_ndvi = df_combined[
        [
            "date",
            "local_std_time",
            "doy_rgb",
            "filename_rgb",
            "filename_ir",
            "solar_elev_rgb",
            "exposure_rgb",
            "exposure_ir",
            "mask_index_rgb",
            "r_mean",
            "g_mean",
            "b_mean",
            "ir_mean",
            "gcc",
            "Y",
            "Z_prime",
            "R_prime",
            "Y_prime",
            "X_prime",
            "NDVI_c",
        ]
    ]

    # rename some columns
    df_ndvi = df_ndvi.rename(
        columns={
            "doy_rgb": "doy",
            "solar_elev_rgb": "solar_elev",
            "mask_index_rgb": "mask_index",
        }
    )

    if not dryrun:
        writeCSV(roits, df_ndvi, outpath)


def writeCSV(roits, df_ndvi, fpath):
    """
    Write NDVI csv using the rgb ROI timeseries header information and
    the combined dataframe.
    """

    # write header
    hdstrings = []
    hdstrings.append("#\n")
    hdstrings.append("# NDVI statistics timeseries for {0}\n".format(roits.site))
    hdstrings.append("#\n")
    hdstrings.append("# Site: {0}\n".format(roits.site))
    hdstrings.append("# Veg Type: {0}\n".format(roits.roitype))
    hdstrings.append("# ROI ID Number: {0:04d}\n".format(roits.sequence_number))
    hdstrings.append("# Lat: {0}\n".format(roits.lat))
    hdstrings.append("# Lon: {0}\n".format(roits.lon))
    hdstrings.append("# Elev: {0}\n".format(roits.elev))
    hdstrings.append("# UTC Offset: {0}\n".format(roits.tzoffset))
    hdstrings.append("# Resize Flag: {0}\n".format(roits.resizeFlg))
    hdstrings.append("# Version: 1\n")

    # set create date and time
    created_at = datetime.now()
    created_time = created_at.time()
    hdstrings.append("# Creation Date: {0}\n".format(created_at.date()))
    hdstrings.append(
        "# Creation Time: {0:02d}:{1:02d}:{2:02d}\n".format(
            created_time.hour, created_time.minute, created_time.second
        )
    )

    # set update date and time to same for generate script
    hdstrings.append("# Update Date: {0}\n".format(created_at.date()))
    hdstrings.append(
        "# Update Time: {0:02d}:{1:02d}:{2:02d}\n".format(
            created_time.hour, created_time.minute, created_time.second
        )
    )

    hdstrings.append("#\n")

    # use pandas to write CSV data then prepend header lines
    df_ndvi.to_csv(fpath, sep=",", na_rep="NA", float_format="%.4f", index=False)

    with open(fpath, "r+") as fh:
        content = fh.read()
        fh.seek(0, 0)
        for line in hdstrings:
            fh.write(line)
        fh.write(content)


# run main when called from command line
if __name__ == "__main__":
    main()
