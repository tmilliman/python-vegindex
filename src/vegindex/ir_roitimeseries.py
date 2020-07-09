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

    if retval == -9999.0:
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


def get_roi_IR_stats(im, roimask):
    """
    Function to return a more extensive collection of stats for DN
    values for an IR image / mask pair.  NOTE: probably move this to
    utils.py.
    """

    # split into bands (for IR images all the bands should be the same.)
    try:
        (im_ir, im_2, im_3) = im.split()
    except ValueError:
        sys.stderr.write("Wrong image type\n")
        return None

    # create numpy arrays with bands
    ir_array = np.asarray(im_ir, dtype=np.int16)
    array_2 = np.asarray(im_2, dtype=np.int16)
    array_3 = np.asarray(im_3, dtype=np.int16)
    brt_array = ir_array + array_2 + array_3

    # check that the image isn't nearly all black or all white in
    # which case getting the stats fails.  Eliminate the outer 30
    # pixels in case there is a banner/overlay on the image.
    #
    # NOTE: this is using almost entire image not just ROI

    if brt_array[30:-30, 30:-30].mean() < 30.0:
        warningstr = "WARNING: mostly dark image.\n"
        sys.stderr.write(warningstr)
        ir_mean = ND_FLOAT
        ir_std = ND_FLOAT
        ir_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT]
        return {"mean": ir_mean, "stdev": ir_std, "percentiles": ir_pcts}

    if brt_array[30:-30, 30:-30].mean() > 725.0:
        warningstr = "WARNING: mostly white image.\n"
        sys.stderr.write(warningstr)
        ir_mean = ND_FLOAT
        ir_std = ND_FLOAT
        ir_pcts = [ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT, ND_FLOAT]
        return {"mean": ir_mean, "stdev": ir_std, "percentiles": ir_pcts}

    # try applying mask to ir image ... if mask and image don't
    # have same size this will raise an exception.
    try:
        ir_ma = np.ma.array(ir_array, mask=roimask)
    except Exception as inst:
        print(inst)
        errstr = "Error applying mask to image file.\n"
        sys.stderr.write(errstr)
        return None

    # find mean and std values
    ir_vals = ir_ma.compressed()
    ir_mean = ir_vals.mean()
    ir_diff = np.float64(ir_vals) - ir_mean
    ir_std = np.sqrt(np.dot(ir_diff, ir_diff) / ir_vals.size)

    # calculate percentiles for each array
    ir_pcts = np.percentile(ir_vals, (5.0, 10.0, 25.0, 50.0, 75.0, 90.0, 95.0))

    # if the above calculation can return a NaN then
    # I should probably trap that here and return a

    # return list of values
    return {"mean": ir_mean, "stdev": ir_std, "percentiles": ir_pcts}


######################################################################


def get_im_metadata(impath):
    """
    look for a matching metadata file and return values in a
    dictionary
    """

    metadata_path = os.path.splitext(impath)[0] + ".meta"
    meta_dict = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as infile:
            for line in infile:
                try:
                    key, value = line.split("=")
                    meta_dict[key] = value.rstrip()
                except ValueError:
                    pass

        # make sure we got some key/value pairs
        if any(meta_dict):
            return meta_dict
        else:
            return None

    else:
        return None


######################################################################


def _filter_comments(f):
    """
    filter comments from csv file
    """
    for line in f:
        line = line.rstrip()
        if line and not line.startswith("#"):
            yield line


def _get_comments(f):
    """
    return JUST the comment lines from a csv file
    """
    for line in f:
        line = line.rstrip()
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
    pattern = r"# {0}:\ (?P<var_value>.+)$".format(var_string)

    var_value = ""
    for line in comments:

        result = re.match(pattern, line)

        if result is not None:
            var_value = result.group("var_value")
            break

    return var_value


class IRROITimeSeries(object):
    """
    Class for CSV version of an IR ROI Timeseries.  There is
    currently no equivalent dB table for an ROI time series
    object.

    Here's a proposed sample IR ROITimeSeries CSV file format:

        #
        # ROI IR statistics timeseries for arbutuslake
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
        date,local_std_time,doy,filename,solar_elev,exposure,mask_index,\
        ir_mean,ir_std,ir_5_qtl,ir_10_qtl,ir_25_qtl,ir_50_qtl,ir_75_qtl,\
        ir_90_qtl,ir_95_qtl \


    """

    def __init__(self, site="", ROIListID="", resizeFlag=False):
        """
        create IR ROITimeSeries object
        """

        self.site = site
        self.roilistid = ROIListID
        self.resizeFlg = resizeFlag
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.rows = []

        # split ROIListID into roitype, and sequence_number
        roitype, sequence_number = ROIListID.split("_")
        self.roitype = roitype
        self.sequence_number = int(sequence_number)

        # grab site info ... really should be a separate
        # class for site with all the site info ... should
        # figure out how to use Django classes here
        if site:
            si = utils.getsiteinfo(site)
            if si is None:
                si = {"lat": None, "lon": None, "elev": None, "tzoffset": None}
        else:
            si = {"lat": None, "lon": None, "elev": None, "tzoffset": None}

        self.lat = si["lat"]
        self.lon = si["lon"]
        self.elev = si["elev"]
        self.tzoffset = si["tzoffset"]

    def get_image_list(self):
        """
        return list of images in an ROI timeseries
        """
        imglist = [row["filename"] for row in self.rows]

        return imglist

    def create_row(self, impath, roimask, mask_index):
        """
        create an IR ROITimeSeries row dictionary for a given image and
        ROI mask.
        """

        # extract datetime from filename
        img_file = os.path.basename(impath)
        img_DT = utils.fn2datetime(self.site, img_file, irFlag=True)
        img_date = img_DT.date()
        img_time = img_DT.time()

        # get doy
        # img_doy = img_DT.timetuple().tm_yday

        # find sun elevation (degrees)
        sun_elev = utils.sunelev(self.lat, self.lon, img_DT, self.tzoffset)

        # Try to load image
        try:
            im = Image.open(impath, "r")
            im.load()
        except IOError:
            errstr1 = "Unable to open file: %s\n" % (impath,)
            errstr2 = "Skipping this file.\n"
            sys.stderr.write(errstr1)
            sys.stderr.write(errstr2)
            return None

        # Try to load image metadata file
        im_metadata = get_im_metadata(impath)

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
            roistats_list = get_roi_IR_stats(im, roimask)

        except KeyboardInterrupt:
            sys.exit()
        except Exception as inst:
            print(inst)
            errstr1 = (
                "Problem getting ROI "
                + "stats for file in create_row(): {0}\n".format(impath)
            )
            sys.stderr.write(errstr1)
            return None

        # get_roi_IR_stats returns None if can't get stats (probably
        # should just throw exception in which case it would be caught
        # by above except clause

        if not (roistats_list):
            return None

        # extract stats
        ir_stats = roistats_list

        ir_mean = ir_stats["mean"]
        ir_std = ir_stats["stdev"]
        ir_5, ir_10, ir_25, ir_50, ir_75, ir_90, ir_95 = ir_stats["percentiles"]

        # get exposure - if None just set to missing value
        if im_metadata is not None:
            exposure = int(im_metadata["exposure"])
        else:
            exposure = ND_INT

        # get awb flag - if None just set to missing value
        try:
            awbflag = int(im_metadata["balance"])

        except Exception:
            awbflag = ND_INT

        # make a structure for the roi IR timeseries
        roits_row = {
            "date": img_date,
            "local_std_time": img_time,
            "datetime": img_DT,
            "ir_mean": ir_mean,
            "ir_std": ir_std,
            "ir_5_qtl": ir_5,
            "ir_10_qtl": ir_10,
            "ir_25_qtl": ir_25,
            "ir_50_qtl": ir_50,
            "ir_75_qtl": ir_75,
            "ir_90_qtl": ir_90,
            "ir_95_qtl": ir_95,
            "filename": "%s" % (img_file,),
            "mask_index": mask_index,
            "solar_elev": sun_elev,
            "exposure": exposure,
            "awbflag": awbflag,
        }

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
        rowfn = roits_row["filename"]
        FN_INDEX = [row["filename"] for row in self.rows]
        try:
            row_index = FN_INDEX.index(rowfn)
        except ValueError:
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

        row_dt = roits_row["datetime"]
        row_doy = row_dt.timetuple().tm_yday

        ir_pcts = [
            roits_row["ir_5_qtl"],
            roits_row["ir_10_qtl"],
            roits_row["ir_25_qtl"],
            roits_row["ir_50_qtl"],
            roits_row["ir_75_qtl"],
            roits_row["ir_90_qtl"],
            roits_row["ir_95_qtl"],
        ]

        csvstr_0 = "{},{},{},{},{:.5f},{},{},{}"
        csvstr_0 = csvstr_0.format(
            roits_row["date"],
            roits_row["local_std_time"],
            row_doy,
            roits_row["filename"],
            roits_row["solar_elev"],
            roits_row["exposure"],
            roits_row["awbflag"],
            roits_row["mask_index"],
        )

        # infrared
        if roits_row["ir_mean"] == ND_FLOAT:
            csvfmt = "{},{}"
        else:
            csvfmt = "{:.5f},{:.5f}"
        csvstr_1 = csvfmt.format(roits_row["ir_mean"], roits_row["ir_std"])
        if ir_pcts[0] == ND_FLOAT:
            csvfmt = "{}"
        else:
            csvfmt = "{:.0f}"

        csvstr_2 = ",".join(csvfmt.format(k) for k in ir_pcts)

        csvstr = ",".join([csvstr_0, csvstr_1, csvstr_2])

        return csvstr

    def writeCSV(self, file=""):
        """
        Method for writing an IRROITimeSeries to CSV file.  The method
        opens the file for writing.  If no filename is passed
        then write to stdout.
        """
        if file == "":
            fo = sys.stdout
        else:
            fo = open(file, "w")

        # write header
        hdstrings = []
        hdstrings.append("#\n")
        hdstrings.append("# ROI IR statistics timeseries for {0}\n".format(self.site))
        hdstrings.append("#\n")
        hdstrings.append("# Site: {0}\n".format(self.site))
        hdstrings.append("# Veg Type: {0}\n".format(self.roitype))
        hdstrings.append("# ROI ID Number: {0:04d}\n".format(self.sequence_number))
        hdstrings.append("# Lat: {0}\n".format(self.lat))
        hdstrings.append("# Lon: {0}\n".format(self.lon))
        hdstrings.append("# Elev: {0}\n".format(self.elev))
        hdstrings.append("# UTC Offset: {0}\n".format(self.tzoffset))
        hdstrings.append("# Resize Flag: {0}\n".format(self.resizeFlg))
        hdstrings.append("# Version: 1\n")
        hdstrings.append("# Creation Date: {0}\n".format(self.created_at.date()))
        create_time = self.created_at.time()
        hdstrings.append(
            "# Creation Time: {0:02d}:{1:02d}:{2:02d}\n".format(
                create_time.hour, create_time.minute, create_time.second
            )
        )

        # set update date and time
        self.updated_at = datetime.now()
        update_time = self.updated_at.time()
        hdstrings.append("# Update Date: {0}\n".format(self.updated_at.date()))
        hdstrings.append(
            "# Update Time: {0:02d}:{1:02d}:{2:02d}\n".format(
                update_time.hour, update_time.minute, update_time.second
            )
        )
        hdstrings.append("#\n")
        for line in hdstrings:
            fo.write(line)

        # write fields line
        fields_str = (
            "date,local_std_time,doy,filename,solar_elev,"
            + "exposure,awbflag,mask_index,"
            + "ir_mean,ir_std,ir_5_qtl,ir_10_qtl,ir_25_qtl,ir_50_qtl,"
            + "ir_75_qtl,ir_90_qtl,ir_95_qtl\n"
        )
        fo.write(fields_str)

        # sort rows by datetime before writing
        rows = self.rows
        rows_sorted = sorted(rows, key=lambda k: k["datetime"])
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

    def select_rows(
        self,
        tod_min=config.TIME_MIN,
        tod_max=config.TIME_MAX,
        sunelev_min=config.MIN_SUN_ANGLE,
        brt_min=config.MIN_BRT,
        brt_max=config.MAX_BRT,
    ):
        """
        routine to return a list of the rows in self.rows
        which meet the selection criteria for brightness
        and time of day.  Numpy probably has a better (i.e. faster)
        way to do this. Also remove rows where thie image is
        completely black.
        """
        selected_rows = []
        for row in self.rows:
            brt = row["ir_mean"] * 3
            if (
                (row["datetime"].time() < tod_min)
                or (row["datetime"].time() > tod_max)
                or (brt < brt_min)
                or (brt > brt_max)
                or (row["solar_elev"] < sunelev_min)
            ):
                continue
            else:
                selected_rows.append(row)

        rows = sorted(selected_rows, key=lambda k: k["datetime"])

        return rows

    def readCSV(self, roiTimeSeriesPath):
        """
        Method to read ROITimeSeries object from CSV file and return
        a ROITimeSeries object.  If the comment fields are not present
        they must be set before the object can be written.
        """

        # open file for reading
        f = open(roiTimeSeriesPath, "r")

        # get comment lines
        comments = list(_get_comments(f))

        # no validation applied to sitename
        site = _get_comment_field(comments, "Site")
        if site != "":
            self.site = site

        # no validataion applied to ROIListId
        # roilistid = _get_comment_field(comments, 'ROI-id')
        # if roilistid != "":
        #     self.roilistid = roilistid
        roitype = _get_comment_field(comments, "Veg Type")
        roiseqno = _get_comment_field(comments, "ROI ID Number")
        self.roitype = roitype
        self.sequence_number = int(roiseqno)
        self.roilistid = "{0}_{1:04d}".format(roitype, int(roiseqno))

        # get Resize Flag if found in header
        resizeflg = _get_comment_field(comments, "Resize Flag")
        if resizeflg != "":
            # convert to boolean
            if resizeflg == "True":
                self.resizeFlg = True

        # make sure we can form a proper date time from create_date and
        # create_time
        create_date = _get_comment_field(comments, "Creation Date")
        create_time = _get_comment_field(comments, "Creation Time")
        if create_date != "" and create_time != "":
            try:
                (Y, M, D) = create_date.split("-")
                (h, m, s) = create_time.split(":")
                create_dt = datetime(int(Y), int(M), int(D), int(h), int(m), int(s))
                self.created_at = create_dt
            except ValueError:
                print("Invalid creation date or time in CSV.")

        # make sure we can form a proper date time from update_date and
        # update_time
        update_date = _get_comment_field(comments, "Update Date")
        update_time = _get_comment_field(comments, "Update Time")
        if update_date != "" and update_time != "":
            try:
                (Y, M, D) = update_date.split("-")
                (h, m, s) = update_time.split(":")
                update_dt = datetime(int(Y), int(M), int(D), int(h), int(m), int(s))
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
            (im_yr, im_mo, im_dom) = row["date"].split("-")
            (im_hr, im_min, im_sec) = row["local_std_time"].split(":")
            im_dt = datetime(
                int(im_yr),
                int(im_mo),
                int(im_dom),
                int(im_hr),
                int(im_min),
                int(im_sec),
            )

            row["datetime"] = im_dt

            # check for awbflag
            if "awbflag" not in row.keys():
                row["awbflag"] = ND_INT

            # check for exposure
            if "exposure" not in row.keys():
                row["exposure"] = ND_INT

            # convert strings to numbers - there's got to be a more
            # efficient way to do this!
            row["solar_elev"] = _float_or_none(row["solar_elev"])
            row["exposure"] = _int_or_none(_float_or_none(row["exposure"]))
            row["awbflag"] = _int_or_none(_float_or_none(row["awbflag"]))
            row["mask_index"] = _int_or_none(row["mask_index"])
            row["ir_mean"] = _float_or_none(row["ir_mean"])
            row["ir_std"] = _float_or_none(row["ir_std"])
            row["ir_5_qtl"] = _float_or_none(row["ir_5_qtl"])
            row["ir_10_qtl"] = _float_or_none(row["ir_10_qtl"])
            row["ir_25_qtl"] = _float_or_none(row["ir_25_qtl"])
            row["ir_50_qtl"] = _float_or_none(row["ir_50_qtl"])
            row["ir_75_qtl"] = _float_or_none(row["ir_75_qtl"])
            row["ir_90_qtl"] = _float_or_none(row["ir_90_qtl"])
            row["ir_95_qtl"] = _float_or_none(row["ir_95_qtl"])
            roitsRows.append(row)

        # do I need to sort here?

        self.rows = roitsRows
        f.close()
