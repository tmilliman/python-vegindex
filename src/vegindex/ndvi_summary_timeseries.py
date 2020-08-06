# -*- coding: utf-8 -*-
from __future__ import print_function

import csv
import re
import sys
from datetime import date
from datetime import datetime
from datetime import time

from . import config
from . import utils

ND_STRING = config.ND_STRING
ND_FLOAT = config.ND_FLOAT
ND_INT = config.ND_INT


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


class NDVISummaryTimeSeries(object):
    """
    Class for CSV version of NDVI summary timeseries.

    Here's a proposed sample NDVISummaryTimeSeries CSV file format:

        #
        # 1-day summary NDVI file for harvardbarn
        #
        # Site: harvardbarn
        # Veg Type: DB
        # ROI ID Number: 1000
        # Lat:
        # Lon:
        # Elev:
        # UTC Offset:
        # Image Count Threshold: 1
        # Aggregation Period: 1
        # Time of Day Min: 00:00:00
        # Time of Day Max: 23:59:59
        # Creation Date: 2013-03-29
        # Creation Time: 12:10:59
        # Update Date: 2013-03-29
        # Update Time: 14:16:43
        # Solar Elevation Min: 5.0
        # ROI Brightness Min: 130
        # ROI Brightness Max: 700
        #
        date,year,doy,image_count,midday_rgb_filename,
          midday_ir_filename,midday_ndvi,gcc_90,ndvi_mean,ndvi_50,ndvi_75,
          ndvi_90,max_solar_elev,snow_flag,outlierflag_ndvi_mean,
          outlierflag_ndvi_50,outlierflag_ndvi_75,outlierflag_ndvi_90

    """

    def __init__(
        self,
        site="",
        ROIListID="",
        nday=1,
        nmin=config.NIMAGE_MIN,
        brt_min=config.MIN_BRT,
        brt_max=config.MAX_BRT,
        tod_min=time(0, 0, 0),
        tod_max=time(23, 59, 59),
        sunelev_min=config.MIN_SUN_ANGLE,
    ):
        """ create NDVISummaryTimeSeries object """

        self.site = site
        self.roilistid = ROIListID
        self.nmin = nmin
        self.tod_min = tod_min
        self.tod_max = tod_max
        self.nday = nday
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.sunelev_min = sunelev_min
        self.brt_min = brt_min
        self.brt_max = brt_max
        self.rows = []

        # get roitype and sequence_number from roilistid
        roitype, roiseqno = self.roilistid.split("_")
        self.roitype = roitype
        self.sequence_number = roiseqno

        if site:
            try:
                si = utils.getsiteinfo(site)
            except ValueError:
                si = {"lat": None, "lon": None, "elev": None, "tzoffset": None}
        else:
            si = {"lat": None, "lon": None, "elev": None, "tzoffset": None}

        self.lat = si["lat"]
        self.lon = si["lon"]
        self.elev = si["elev"]
        self.tzoffset = si["tzoffset"]

    def readCSV(self, ndvi_summary_path):
        """
        Method to read NDVISummaryTimeSeries object from CSV file and return
        a NDVISummaryTimeSeries object.
        """

        # open file for reading
        f = open(ndvi_summary_path, "r")

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
        roilistid = roitype + "_" + roiseqno
        self.roilistid = roilistid
        self.roitype = roitype
        self.sequence_number = roiseqno

        # probably need to read in lat, lon, elev, tz_offset
        # really this should be a "site" class!!!  If you
        # use vegindex.get_ndvi_timeseries it should work.

        # Image Count Threshold: 1
        nmin = _get_comment_field(comments, "Image Count Threshold")
        if nmin != "":
            self.nmin = int(nmin)

        # Aggregation Period: 1
        nday = _get_comment_field(comments, "Aggregation Period")
        if nday != "":
            self.nday = int(nday)

        # Time of Day Min: 00:00:00
        time_str = _get_comment_field(comments, "Time of Day Min")
        if time_str != "":
            [hr_str, min_str, sec_str] = time_str.split(":")
            self.tod_min = time(int(hr_str), int(min_str), int(sec_str))

        # Time of Day Max: 23:59:59
        time_str = _get_comment_field(comments, "Time of Day Max")
        if time_str != "":
            [hr_str, min_str, sec_str] = time_str.split(":")
            self.tod_max = time(int(hr_str), int(min_str), int(sec_str))

        # Solar Elevation Min: 5.0
        sunelev_min_str = _get_comment_field(comments, "Solar Elevation Min")
        if sunelev_min_str != "":
            self.sunelev_min = float(sunelev_min_str)

        # ROI Brightness Min: 130
        brt_min_str = _get_comment_field(comments, "ROI Brightness Min")
        if brt_min_str != "":
            self.brt_min = int(brt_min_str)

        # ROI Brightness Max: 700
        brt_max_str = _get_comment_field(comments, "ROI Brightness Max")
        if brt_max_str != "":
            self.brt_max = int(brt_max_str)

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

        # get timeseries rows
        f.seek(0)
        csvrdr = csv.DictReader(_filter_comments(f))

        ndvisummary_rows = []
        for row in csvrdr:

            # convert date string to date object
            [yr_str, mo_str, dom_str] = row["date"].split("-")
            ndvi_date = date(int(yr_str), int(mo_str), int(dom_str))
            row["date"] = ndvi_date
            row["year"] = ndvi_date.year

            # turn strings to numbers checking for empty/missing and
            # no-data values
            row["image_count"] = int(row["image_count"])

            if row["image_count"] == 0:
                row["doy"] = _int_or_none(row["doy"])
                row["midday_rgb_filename"] = ND_STRING
                row["midday_ir_filename"] = ND_STRING
                row["midday_ndvi"] = ND_FLOAT
                row["gcc_mean"] = ND_FLOAT
                row["ndvi_mean"] = ND_FLOAT
                row["ndvi_std"] = ND_FLOAT
                row["ndvi_50"] = ND_FLOAT
                row["ndvi_75"] = ND_FLOAT
                row["ndvi_90"] = ND_FLOAT
                row["max_solar_elev"] = ND_FLOAT
                row["snow_flag"] = ND_INT
                row["outlierflag_ndvi_mean"] = ND_INT
                row["outlierflag_ndvi_50"] = ND_INT
                row["outlierflag_ndvi_75"] = ND_INT
                row["outlierflag_ndvi_90"] = ND_INT

            elif row["image_count"] < self.nmin:
                row["doy"] = _int_or_none(row["doy"])
                if not row["midday_rgb_filename"]:
                    row["midday_rgb_filename"] = ND_STRING
                if not row["midday_ir_filename"]:
                    row["midday_ir_filename"] = ND_STRING
                row["midday_ndvi"] = _float_or_none(row["midday_ndvi"])
                row["gcc_90"] = _float_or_none(row["gcc_90"])
                row["ndvi_mean"] = _float_or_none(row["ndvi_mean"])
                row["ndvi_std"] = _float_or_none(row["ndvi_std"])
                row["ndvi_50"] = ND_FLOAT
                row["ndvi_75"] = ND_FLOAT
                row["ndvi_90"] = ND_FLOAT
                row["max_solar_elev"] = ND_FLOAT
                row["snow_flag"] = ND_INT
                row["outlierflag_ndvi_mean"] = ND_INT
                row["outlierflag_ndvi_50"] = ND_INT
                row["outlierflag_ndvi_75"] = ND_INT
                row["outlierflag_ndvi_90"] = ND_INT

            else:
                row["doy"] = _int_or_none(row["doy"])
                row["midday_ndvi"] = _float_or_none(row["midday_ndvi"])
                row["gcc_90"] = _float_or_none(row["gcc_90"])
                row["ndvi_mean"] = _float_or_none(row["ndvi_mean"])
                row["ndvi_std"] = _float_or_none(row["ndvi_std"])
                row["ndvi_50"] = _float_or_none(row["ndvi_50"])
                row["ndvi_75"] = _float_or_none(row["ndvi_75"])
                row["ndvi_90"] = _float_or_none(row["ndvi_90"])
                row["max_solar_elev"] = _float_or_none(row["max_solar_elev"])
                row["snow_flag"] = _int_or_none(row["snow_flag"])
                row["outlierflag_ndvi_mean"] = _int_or_none(
                    row["outlierflag_ndvi_mean"]
                )
                row["outlierflag_ndvi_50"] = _int_or_none(row["outlierflag_ndvi_50"])
                row["outlierflag_ndvi_75"] = _int_or_none(row["outlierflag_ndvi_75"])
                row["outlierflag_ndvi_90"] = _int_or_none(row["outlierflag_ndvi_90"])

            ndvisummary_rows.append(row)

        self.rows = ndvisummary_rows

    def insert_row(
        self,
        date,
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
    ):
        """
        create a NDVISummaryTimeSeries row dictionary for a particluar date
        insert it into self.rows list and return the row dictionary.
        """

        # create a row dictionary
        year = date.year
        ndvits_row = {
            "date": date,
            "year": year,
            "doy": doy,
            "image_count": image_count,
            "midday_rgb_filename": midday_rgb_filename,
            "midday_ir_filename": midday_ir_filename,
            "midday_ndvi": midday_ndvi,
            "gcc_90": gcc_90,
            "ndvi_mean": ndvi_mean,
            "ndvi_std": ndvi_std,
            "ndvi_50": ndvi_50,
            "ndvi_75": ndvi_75,
            "ndvi_90": ndvi_90,
            "max_solar_elev": max_solar_elev,
            "snow_flag": snow_flag,
            "outlierflag_ndvi_mean": outlierflag_ndvi_mean,
            "outlierflag_ndvi_50": outlierflag_ndvi_50,
            "outlierflag_ndvi_75": outlierflag_ndvi_75,
            "outlierflag_ndvi_90": outlierflag_ndvi_90,
        }

        # use date as key
        DT_INDEX = [row["date"] for row in self.rows]
        try:
            row_index = DT_INDEX.index(date)
        except ValueError:
            row_index = None

        # replace or append
        if row_index:
            self.rows.pop(row_index)
            self.rows.append(ndvits_row)
        else:
            self.rows.append(ndvits_row)

        return ndvits_row

    def format_csvrow(self, ndvi_summary_ts_row):

        """
        Format NDVISummaryTimeSeries CSV row as string.  To handle
        no-data/missing values using strings like 'NA' or 'NULL' we
        use different formats depending on whether there is missing
        data or not.  The problem is that a fixed format field for
        real numbers {:.5f} doesn't handle a string like NA.
        """

        if ndvi_summary_ts_row["image_count"] >= self.nmin:
            line_format = (
                "{0},{1},{2},{3},{4},{5},"
                + "{6:.5f},{7:.5f},{8:.5f},{9:.5f},"
                + "{10:.5f},{11:.5f},{12:.5f},{13:.5f},"
                + "{14},{15},{16},{17},{18}"
            )

        # case where there are some images but less than the threshold to
        # print a aggregate value
        elif (ndvi_summary_ts_row["image_count"] < self.nmin) and (
            ndvi_summary_ts_row["image_count"] > 0
        ):
            line_format = (
                "{0},{1},{2},{3},{4},{5},"
                + "{6},{7},{8},{9},"
                + "{10},{11},{12},{13},"
                + "{14},{15},{16},{17},{18}"
            )

        # case where there are no images for this time period
        else:
            line_format = (
                "{0},{1},{2},{3},{4},{5},"
                + "{6},{7},{8},{9},"
                + "{10},{11},{12},{13},"
                + "{14},{15},{16},{17},{18}"
            )

        csvstr = line_format.format(
            ndvi_summary_ts_row["date"],
            ndvi_summary_ts_row["year"],
            ndvi_summary_ts_row["doy"],
            ndvi_summary_ts_row["image_count"],
            ndvi_summary_ts_row["midday_rgb_filename"],
            ndvi_summary_ts_row["midday_ir_filename"],
            ndvi_summary_ts_row["midday_ndvi"],
            ndvi_summary_ts_row["gcc_90"],
            ndvi_summary_ts_row["ndvi_mean"],
            ndvi_summary_ts_row["ndvi_std"],
            ndvi_summary_ts_row["ndvi_50"],
            ndvi_summary_ts_row["ndvi_75"],
            ndvi_summary_ts_row["ndvi_90"],
            ndvi_summary_ts_row["max_solar_elev"],
            ndvi_summary_ts_row["snow_flag"],
            ndvi_summary_ts_row["outlierflag_ndvi_mean"],
            ndvi_summary_ts_row["outlierflag_ndvi_50"],
            ndvi_summary_ts_row["outlierflag_ndvi_75"],
            ndvi_summary_ts_row["outlierflag_ndvi_90"],
        )

        return csvstr

    def writeCSV(self, file=""):
        """
        Method for writing NDVISummaryTimeSeries to CSV file.  The method
        opens the file, file, for writing.  If no file object is
        passed write to standard out.

        Do we need to be careful to avoid overwriting files?

        """

        if file == "":
            fo = sys.stdout
        else:
            fo = open(file, "w")

        # write header
        hdstrings = []
        hdstrings.append("#\n")
        hdstrings.append(
            ("# {0}-day NDVI summary time" + "series for {1}\n").format(
                self.nday, self.site
            )
        )
        hdstrings.append("#\n")
        hdstrings.append("# Site: {0}\n".format(self.site))
        hdstrings.append("# Veg Type: {0}\n".format(self.roitype))
        hdstrings.append("# ROI ID Number: {0}\n".format(self.sequence_number))
        hdstrings.append("# Lat: {0}\n".format(self.lat))
        hdstrings.append("# Lon: {0}\n".format(self.lon))
        hdstrings.append("# Elev: {0}\n".format(self.elev))
        hdstrings.append("# UTC Offset: {0}\n".format(self.tzoffset))
        hdstrings.append("# Image Count Threshold: {0}\n".format(self.nmin))
        hdstrings.append("# Aggregation Period: {0}\n".format(self.nday))
        hdstrings.append("# Solar Elevation Min: {0}\n".format(self.sunelev_min))
        hdstrings.append("# Time of Day Min: {0}\n".format(self.tod_min))
        hdstrings.append("# Time of Day Max: {0}\n".format(self.tod_max))
        hdstrings.append("# ROI Brightness Min: {0}\n".format(self.brt_min))
        hdstrings.append("# ROI Brightness Max: {0}\n".format(self.brt_max))
        hdstrings.append("# Creation Date: {0}\n".format(self.created_at.date()))
        create_time = self.created_at.time()
        create_time_str = "# Creation Time: {0:02d}:{1:02d}:{2:02d}\n"
        hdstrings.append(
            create_time_str.format(
                create_time.hour, create_time.minute, create_time.second
            )
        )
        # set update time to now
        self.updated_at = datetime.now()
        update_time = self.updated_at.time()
        hdstrings.append("# Update Date: {0}\n".format(self.updated_at.date()))
        update_time_str = "# Update Time: {0:02d}:{1:02d}:{2:02d}\n"
        hdstrings.append(
            update_time_str.format(
                update_time.hour, update_time.minute, update_time.second
            )
        )
        hdstrings.append("#\n")

        for line in hdstrings:
            fo.write(line)

        # sort rows by datetime before writing
        rows = self.rows
        rows_sorted = sorted(rows, key=lambda k: k["date"])
        self.rows = rows_sorted

        # set up fieldnames - this should be in a global!
        ndvits_fn = [
            "date",
            "year",
            "doy",
            "image_count",
            "midday_rgb_filename",
            "midday_ir_filename",
            "midday_ndvi",
            "gcc_90",
            "ndvi_mean",
            "ndvi_std",
            "ndvi_50",
            "ndvi_75",
            "ndvi_90",
            "max_solar_elev",
            "snow_flag",
            "outlierflag_ndvi_mean",
            "outlierflag_ndvi_50",
            "outlierflag_ndvi_75",
            "outlierflag_ndvi_90",
        ]

        #
        # create csvwriter
        csvwriter = csv.DictWriter(
            fo,
            delimiter=",",
            fieldnames=ndvits_fn,
            lineterminator="\n",
            quoting=csv.QUOTE_NONE,
        )

        # write header
        csvwriter.writerow(dict((fn, fn) for fn in ndvits_fn))
        # csvwriter.writeheader()

        # write ndvi ts data
        for row in self.rows:

            # format row
            formatted_row = row
            if row["image_count"] >= self.nmin:
                formatted_row["midday_ndvi"] = "{0:.5f}".format(row["midday_ndvi"])
                formatted_row["gcc_90"] = "{0:.5f}".format(row["gcc_90"])
                formatted_row["ndvi_mean"] = "{0:.5f}".format(row["ndvi_mean"])
                formatted_row["ndvi_std"] = "{0:.5f}".format(row["ndvi_std"])
                formatted_row["ndvi_50"] = "{0:.5f}".format(row["ndvi_50"])
                formatted_row["ndvi_75"] = "{0:.5f}".format(row["ndvi_75"])
                formatted_row["ndvi_90"] = "{0:.5f}".format(row["ndvi_90"])
                formatted_row["max_solar_elev"] = "{0:.5f}".format(
                    row["max_solar_elev"]
                )
            csvwriter.writerow(formatted_row)

        # close file
        if not file == "":
            fo.close()

        # return number of rows
        return len(self.rows)
