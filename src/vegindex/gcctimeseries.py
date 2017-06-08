# -*- coding: utf-8 -*-

import config
import csv
import re
import sys
from datetime import date
from datetime import datetime
from datetime import time

from . import utils

ND_STRING = config.ND_STRING
ND_FLOAT = config.ND_FLOAT
ND_INT = config.ND_INT


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


class GCCTimeSeries(object):
    """
    Class for CSV version of GCC Timeseries.  There is currently
    no equivalent dB table for the GCC time series object.

    Here's a proposed sample GCCTimeSeries CSV file format:

        #
        # 1-day summary product file for harvardbarn
        #
        # Site: harvardbarn
        # Veg Type: DB
        # ROI ID Number: 0001
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
        date,year,doy,image_count,midday_filename,midday_r,midday_g,
        midday_b,midday_gcc,midday_rcc,r_mean,r_std,g_mean,g_std,
        b_mean,g_std,gcc_mean,gcc_std,gcc_50,gcc_75,gcc_90,
        rcc_mean,rcc_std,rcc_50,rcc_75,rcc_90, max_solar_elev,
        snow_flag,outlierflag_gcc_mean,
        outlierflag_gcc_50,outlierflag_gcc_75,outlierflag_gcc_90

    """

    def __init__(self, site='', ROIListID='', nday=1,
                 nmin=config.NIMAGE_MIN,
                 brt_min=config.MIN_BRT,
                 brt_max=config.MAX_BRT,
                 tod_min=time(0, 0, 0),
                 tod_max=time(23, 59, 59),
                 sunelev_min=config.MIN_SUN_ANGLE):
        """ create GCCTimeSeries object """

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
        roitype, roiseqno = self.roilistid.split('_')
        self.roitype = roitype
        self.sequence_number = roiseqno

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

    def readCSV(self, gccTimeSeriesPath):
        """
        Method to read GCCTimeSeries object from CSV file and return
        a GCCTimeSeries object.
        """

        # open file for reading
        f = open(gccTimeSeriesPath, 'r')

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
        roilistid = roitype + "_" + roiseqno
        self.roilistid = roilistid
        self.roitype = roitype
        self.sequence_number = roiseqno

        # probably need to read in lat, lon, elev, tz_offset
        # really this should be a "site" class!!!  If you
        # use vegindex.get_gcc_timeseries it should work.

        # Image Count Threshold: 1
        nmin = _get_comment_field(comments, 'Image Count Threshold')
        if nmin != "":
            self.nmin = int(nmin)

        # Aggregation Period: 1
        nday = _get_comment_field(comments, 'Aggregation Period')
        if nday != "":
            self.nday = int(nday)

        # Time of Day Min: 00:00:00
        time_str = _get_comment_field(comments, 'Time of Day Min')
        if time_str != "":
            [hr_str, min_str, sec_str] = time_str.split(':')
            self.tod_min = time(int(hr_str), int(min_str), int(sec_str))

        # Time of Day Max: 23:59:59
        time_str = _get_comment_field(comments, 'Time of Day Max')
        if time_str != "":
            [hr_str, min_str, sec_str] = time_str.split(':')
            self.tod_max = time(int(hr_str), int(min_str), int(sec_str))

        # Solar Elevation Min: 5.0
        sunelev_min_str = _get_comment_field(comments,
                                             'Solar Elevation Min')
        if sunelev_min_str != "":
            self.sunelev_min = float(sunelev_min_str)

        # ROI Brightness Min: 130
        brt_min_str = _get_comment_field(comments, 'ROI Brightness Min')
        if brt_min_str != "":
            self.brt_min = int(brt_min_str)

        # ROI Brightness Max: 700
        brt_max_str = _get_comment_field(comments, 'ROI Brightness Max')
        if brt_max_str != "":
            self.brt_max = int(brt_max_str)

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
                print "Invalid creation date or time in CSV."

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
                print "Invalid update date or time in CSV."

        # get timeseries rows
        f.seek(0)
        csvrdr = csv.DictReader(_filter_comments(f))

        gcctsRows = []
        for row in csvrdr:

            # convert date string to date object
            [yr_str, mo_str, dom_str] = row['date'].split('-')
            gcc_date = date(int(yr_str), int(mo_str), int(dom_str))
            row['date'] = gcc_date
            row['year'] = gcc_date.year

            # turn strings to numbers checking for empty/missing and
            # no-data values
            row['image_count'] = int(row['image_count'])

            if row['image_count'] == 0:
                row['doy'] = _int_or_none(row['doy'])
                row['midday_filename'] = ND_STRING
                row['midday_r'] = ND_FLOAT
                row['midday_g'] = ND_FLOAT
                row['midday_b'] = ND_FLOAT
                row['midday_gcc'] = ND_FLOAT
                row['midday_rcc'] = ND_FLOAT
                row['r_mean'] = ND_FLOAT
                row['r_std'] = ND_FLOAT
                row['g_mean'] = ND_FLOAT
                row['g_std'] = ND_FLOAT
                row['b_mean'] = ND_FLOAT
                row['b_std'] = ND_FLOAT
                row['gcc_mean'] = ND_FLOAT
                row['gcc_std'] = ND_FLOAT
                row['gcc_50'] = ND_FLOAT
                row['gcc_75'] = ND_FLOAT
                row['gcc_90'] = ND_FLOAT
                row['rcc_mean'] = ND_FLOAT
                row['rcc_std'] = ND_FLOAT
                row['rcc_50'] = ND_FLOAT
                row['rcc_75'] = ND_FLOAT
                row['rcc_90'] = ND_FLOAT
                row['max_solar_elev'] = ND_FLOAT
                row['snow_flag'] = ND_INT
                row['outlierflag_gcc_mean'] = ND_INT
                row['outlierflag_gcc_50'] = ND_INT
                row['outlierflag_gcc_75'] = ND_INT
                row['outlierflag_gcc_90'] = ND_INT

            elif row['image_count'] < self.nmin:
                row['doy'] = _int_or_none(row['doy'])
                if not row['midday_filename']:
                    row['midday_filename'] = ND_STRING
                row['midday_r'] = _float_or_none(row['midday_r'])
                row['midday_g'] = _float_or_none(row['midday_g'])
                row['midday_b'] = _float_or_none(row['midday_b'])
                row['midday_gcc'] = _float_or_none(row['midday_gcc'])
                row['midday_rcc'] = _float_or_none(row['midday_rcc'])
                row['r_mean'] = ND_FLOAT
                row['r_std'] = ND_FLOAT
                row['g_mean'] = ND_FLOAT
                row['g_std'] = ND_FLOAT
                row['b_mean'] = ND_FLOAT
                row['b_std'] = ND_FLOAT
                row['gcc_mean'] = ND_FLOAT
                row['gcc_std'] = ND_FLOAT
                row['gcc_50'] = ND_FLOAT
                row['gcc_75'] = ND_FLOAT
                row['gcc_90'] = ND_FLOAT
                row['rcc_mean'] = ND_FLOAT
                row['rcc_std'] = ND_FLOAT
                row['rcc_50'] = ND_FLOAT
                row['rcc_75'] = ND_FLOAT
                row['rcc_90'] = ND_FLOAT
                row['max_solar_elev'] = ND_FLOAT
                row['snow_flag'] = ND_INT
                row['outlierflag_gcc_mean'] = ND_INT
                row['outlierflag_gcc_50'] = ND_INT
                row['outlierflag_gcc_75'] = ND_INT
                row['outlierflag_gcc_90'] = ND_INT

            else:
                row['doy'] = _int_or_none(row['doy'])
                row['midday_r'] = _float_or_none(row['midday_r'])
                row['midday_g'] = _float_or_none(row['midday_g'])
                row['midday_b'] = _float_or_none(row['midday_b'])
                row['midday_gcc'] = _float_or_none(row['midday_gcc'])
                row['midday_rcc'] = _float_or_none(row['midday_rcc'])
                row['r_mean'] = _float_or_none(row['r_mean'])
                row['r_std'] = _float_or_none(row['r_std'])
                row['g_mean'] = _float_or_none(row['g_mean'])
                row['g_std'] = _float_or_none(row['g_std'])
                row['b_mean'] = _float_or_none(row['b_mean'])
                row['b_std'] = _float_or_none(row['b_std'])
                row['gcc_mean'] = _float_or_none(row['gcc_mean'])
                row['gcc_std'] = _float_or_none(row['gcc_std'])
                row['gcc_50'] = _float_or_none(row['gcc_50'])
                row['gcc_75'] = _float_or_none(row['gcc_75'])
                row['gcc_90'] = _float_or_none(row['gcc_90'])
                row['rcc_mean'] = _float_or_none(row['rcc_mean'])
                row['rcc_std'] = _float_or_none(row['rcc_std'])
                row['rcc_50'] = _float_or_none(row['rcc_50'])
                row['rcc_75'] = _float_or_none(row['rcc_75'])
                row['rcc_90'] = _float_or_none(row['rcc_90'])
                row['max_solar_elev'] = _float_or_none(row['max_solar_elev'])
                row['snow_flag'] = _int_or_none(row['snow_flag'])
                row['outlierflag_gcc_mean'] = _int_or_none(
                    row['outlierflag_gcc_mean'])
                row['outlierflag_gcc_50'] = _int_or_none(
                    row['outlierflag_gcc_50'])
                row['outlierflag_gcc_75'] = _int_or_none(
                    row['outlierflag_gcc_75'])
                row['outlierflag_gcc_90'] = _int_or_none(
                    row['outlierflag_gcc_90'])

            gcctsRows.append(row)

        self.rows = gcctsRows

    def insert_row(self, date, doy, image_count,
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
                   outlierflag_gcc_90):
        """
        create a GCCTimeSeries row dictionary for a particluar date
        insert it into self.rows list and return the row dictionary.
        """

        # create a row dictionary
        year = date.year
        gccts_row = {'date': date,
                     'year': year,
                     'doy': doy,
                     'image_count': image_count,
                     'midday_filename': midday_filename,
                     'midday_r': midday_r,
                     'midday_g': midday_g,
                     'midday_b': midday_b,
                     'midday_gcc': midday_gcc,
                     'midday_rcc': midday_rcc,
                     'r_mean': r_mean,
                     'r_std': r_std,
                     'g_mean': g_mean,
                     'g_std': g_std,
                     'b_mean': b_mean,
                     'b_std': b_std,
                     'gcc_mean': gcc_mean,
                     'gcc_std': gcc_std,
                     'gcc_50': gcc_50,
                     'gcc_75': gcc_75,
                     'gcc_90': gcc_90,
                     'rcc_mean': rcc_mean,
                     'rcc_std': rcc_std,
                     'rcc_50': rcc_50,
                     'rcc_75': rcc_75,
                     'rcc_90': rcc_90,
                     'max_solar_elev': max_solar_elev,
                     'snow_flag': snow_flag,
                     'outlierflag_gcc_mean': outlierflag_gcc_mean,
                     'outlierflag_gcc_50': outlierflag_gcc_50,
                     'outlierflag_gcc_75': outlierflag_gcc_75,
                     'outlierflag_gcc_90': outlierflag_gcc_90}

        # use date as key
        DT_INDEX = [row['date'] for row in self.rows]
        try:
            row_index = DT_INDEX.index(date)
        except:
            row_index = None

        # replace or append
        if row_index:
            self.rows.pop(row_index)
            self.rows.append(gccts_row)
        else:
            self.rows.append(gccts_row)

        return gccts_row

    def format_csvrow(self, gccts_row):
        """
        Format GCCTimeSeries CSV row as string.  To handle no-data/missing
        values using strings like 'NA' or 'NULL' we use different
        formats depending on whether there is missing data or not.
        The problem is that a fixed format field for real numbers
        {:.5f} doesn't handle a string like NA.

        """

        if gccts_row['image_count'] >= self.nmin:
            line_format = '{0},{1},{2},{3},{4},' + \
                          '{5:.5f},{6:.5f},{7:.5f},{8:.5f},{9:.5f},' + \
                          '{10:.5f},{11:.5f},{12:.5f}, {13:.5f},{14:.5f},' + \
                          '{15:.5f},{16:.5f},{17:.5f},{18:.5f},{19:.5f},' + \
                          '{20:.5f},{21:.5f},{22:.5f},{23:.5f},{24:.5f},' + \
                          '{25:.5f},{26:.5f},{27},{28},{29},' + \
                          '{30},{31}'

        # case where there are some images but less than the threshold to
        # print a aggregate value
        elif ((gccts_row['image_count'] < self.nmin) and
              (gccts_row['image_count'] > 0)):
            line_format = '{0},{1},{2},{3},{4},' + \
                          '{5:.5f},{6:.5f},{7:.5f},{8:.5f},{9:.5f},' + \
                          '{10},{11},{12},{13},{14},' + \
                          '{15},{16},{17},{18},{19},' + \
                          '{20},{21},{22},{23},{24},' + \
                          '{25},{26},{27},{28},{29},' + \
                          '{30},{31}'

        # case where there are no images for this time period
        else:
            line_format = '{0},{1},{2},{3},{4},' + \
                          '{5},{6},{7},{8},{9},' + \
                          '{10},{11},{12},{13},{14},' + \
                          '{15},{16},{17},{18},{19},' + \
                          '{20},{21},{22},{23},{24},' + \
                          '{25},{26},{27},{28},{29},' + \
                          '{30},{31}'

        csvstr = line_format.format(
            gccts_row['date'],
            gccts_row['year'],
            gccts_row['doy'],
            gccts_row['image_count'],
            gccts_row['midday_filename'],
            gccts_row['midday_r'],
            gccts_row['midday_g'],
            gccts_row['midday_b'],
            gccts_row['midday_gcc'],
            gccts_row['midday_rcc'],
            gccts_row['r_mean'],
            gccts_row['r_std'],
            gccts_row['g_mean'],
            gccts_row['g_std'],
            gccts_row['b_mean'],
            gccts_row['b_std'],
            gccts_row['gcc_mean'],
            gccts_row['gcc_std'],
            gccts_row['gcc_50'],
            gccts_row['gcc_75'],
            gccts_row['gcc_90'],
            gccts_row['rcc_mean'],
            gccts_row['rcc_std'],
            gccts_row['rcc_50'],
            gccts_row['rcc_75'],
            gccts_row['rcc_90'],
            gccts_row['max_solar_elev'],
            gccts_row['snow_flag'],
            gccts_row['outlierflag_gcc_mean'],
            gccts_row['outlierflag_gcc_50'],
            gccts_row['outlierflag_gcc_75'],
            gccts_row['outlierflag_gcc_90'])

        return csvstr

    def writeCSV(self, file=""):
        """
        Method for writing GCCTimeSeries to CSV file.  The method opens
        the file, file, for writing.  If no file object is passed
        write to standard out.

        Do we need to be careful to avoid overwriting files?
        """

        if file == "":
            fo = sys.stdout
        else:
            fo = open(file, 'w')

        # write header
        hdstrings = []
        hdstrings.append('#\n')
        hdstrings.append('# {0}-day summary product time' +
                         'series for {1}\n'.format(self.nday, self.site))
        hdstrings.append('#\n')
        hdstrings.append('# Site: {0}\n'.format(self.site))
        hdstrings.append('# Veg Type: {0}\n'.format(self.roitype))
        hdstrings.append('# ROI ID Number: {0}\n'.format(
            self.sequence_number))
        hdstrings.append('# Lat: {0}\n'.format(self.lat))
        hdstrings.append('# Lon: {0}\n'.format(self.lon))
        hdstrings.append('# Elev: {0}\n'.format(self.elev))
        hdstrings.append('# UTC Offset: {0}\n'.format(self.tzoffset))
        hdstrings.append('# Image Count Threshold: {0}\n'.format(self.nmin))
        hdstrings.append('# Aggregation Period: {0}\n'.format(self.nday))
        hdstrings.append('# Solar Elevation Min: {0}\n'.format(
            self.sunelev_min))
        hdstrings.append('# Time of Day Min: {0}\n'.format(self.tod_min))
        hdstrings.append('# Time of Day Max: {0}\n'.format(self.tod_max))
        hdstrings.append('# ROI Brightness Min: {0}\n'.format(self.brt_min))
        hdstrings.append('# ROI Brightness Max: {0}\n'.format(self.brt_max))
        hdstrings.append('# Creation Date: {0}\n'.format(
            self.created_at.date()))
        create_time = self.created_at.time()
        hdstrings.append('# Creation Time: {0:02d}:{1:02d}:' +
                         '{2:02d}\n'.format(create_time.hour,
                                            create_time.minute,
                                            create_time.second))
        # set update time to now
        self.updated_at = datetime.now()
        update_time = self.updated_at.time()
        hdstrings.append('# Update Date: {0}\n'.format(
            self.updated_at.date()))
        hdstrings.append('# Update Time: {0:02d}:{1:02d}:' +
                         '{2:02d}\n'.format(update_time.hour,
                                            update_time.minute,
                                            update_time.second))
        hdstrings.append('#\n')

        for line in hdstrings:
            fo.write(line)

        # sort rows by datetime before writing
        rows = self.rows
        rows_sorted = sorted(rows, key=lambda k: k['date'])
        self.rows = rows_sorted

        # set up fieldnames - this should be in a global!
        gccts_fn = [
            'date',
            'year',
            'doy',
            'image_count',
            'midday_filename',
            'midday_r',
            'midday_g',
            'midday_b',
            'midday_gcc',
            'midday_rcc',
            'r_mean',
            'r_std',
            'g_mean',
            'g_std',
            'b_mean',
            'b_std',
            'gcc_mean',
            'gcc_std',
            'gcc_50',
            'gcc_75',
            'gcc_90',
            'rcc_mean',
            'rcc_std',
            'rcc_50',
            'rcc_75',
            'rcc_90',
            'max_solar_elev',
            'snow_flag',
            'outlierflag_gcc_mean',
            'outlierflag_gcc_50',
            'outlierflag_gcc_75',
            'outlierflag_gcc_90'
        ]

        #
        # create csvwriter
        csvwriter = csv.DictWriter(fo, delimiter=',',
                                   fieldnames=gccts_fn,
                                   lineterminator='\n',
                                   quoting=csv.QUOTE_NONE)

        # write header
        csvwriter.writerow(dict((fn, fn) for fn in gccts_fn))
        # csvwriter.writeheader()

        # write gcc ts data
        for row in self.rows:

            # format row
            formatted_row = row
            if row['image_count'] >= self.nmin:
                formatted_row['midday_r'] = '{0:.5f}'.format(row['midday_r'])
                formatted_row['midday_g'] = '{0:.5f}'.format(row['midday_g'])
                formatted_row['midday_b'] = '{0:.5f}'.format(row['midday_b'])
                formatted_row['midday_gcc'] = '{0:.5f}'.format(
                    row['midday_gcc'])
                formatted_row['midday_rcc'] = '{0:.5f}'.format(
                    row['midday_rcc'])
                formatted_row['r_mean'] = '{0:.5f}'.format(row['r_mean'])
                formatted_row['r_std'] = '{0:.5f}'.format(row['r_std'])
                formatted_row['g_mean'] = '{0:.5f}'.format(row['g_mean'])
                formatted_row['g_std'] = '{0:.5f}'.format(row['g_std'])
                formatted_row['b_mean'] = '{0:.5f}'.format(row['b_mean'])
                formatted_row['b_std'] = '{0:.5f}'.format(row['b_std'])
                formatted_row['gcc_mean'] = '{0:.5f}'.format(row['gcc_mean'])
                formatted_row['gcc_std'] = '{0:.5f}'.format(row['gcc_std'])
                formatted_row['gcc_50'] = '{0:.5f}'.format(row['gcc_50'])
                formatted_row['gcc_75'] = '{0:.5f}'.format(row['gcc_75'])
                formatted_row['gcc_90'] = '{0:.5f}'.format(row['gcc_90'])
                formatted_row['rcc_mean'] = '{0:.5f}'.format(row['rcc_mean'])
                formatted_row['rcc_std'] = '{0:.5f}'.format(row['rcc_std'])
                formatted_row['rcc_50'] = '{0:.5f}'.format(row['rcc_50'])
                formatted_row['rcc_75'] = '{0:.5f}'.format(row['rcc_75'])
                formatted_row['rcc_90'] = '{0:.5f}'.format(row['rcc_90'])
                formatted_row['max_solar_elev'] = '{0:.5f}'.format(
                    row['max_solar_elev'])
            csvwriter.writerow(formatted_row)

        # close file
        if not file == "":
            fo.close()

        # return number of rows
        return len(self.rows)
