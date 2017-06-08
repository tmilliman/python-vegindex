# -*- coding: utf-8 -*-

import config
import csv
import re
import sys
from datetime import datetime


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


class ROIList(object):
    """
    Class for CSV version of ROI List.
    """

    def __init__(self, site='', roitype='', descrip='', sequence_number=0,
                 owner=''):
        """
        create ROIList object which matches database

        Here's a proposed sample ROIList file:

        #
        # ROI List for hubbardbrooknfws
        #
        # Site: hubbardbrooknfws
        # Veg Type: DB
        # ROI ID Number: 0001
        # Owner: mtoomey
        # Creation Date: 2013-02-11
        # Creation Time: 11:19:00
        # Update Date: 2013-02-11
        # Update Time: 11:19:00
        # Description: Full mixed canopy
        #
        start_date,start_time,end_date,end_time,maskfile,sample_image
        2012-09-27,00:00:00,9999-12-31,00:00:00,hubbardbrooknfws_canopy_0001_01.tif,hubbardbrooknfws_2013_02_01_141504.jpg

        """
        self.site = site
        self.roitype = roitype
        self.sequence_number = sequence_number
        self.owner = owner
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.descrip = descrip

        # preform some sanity checks
        if roitype != "":
            try:
                config.ROITypes.index(roitype)
                self.roitype = roitype
            except ValueError:
                sys.stderr.write("Unknown Veg Type in CSV\n")
                raise ValueError

        # sequence number should be decimal
        try:
            self.sequence_number = int(sequence_number)
        except ValueError:
            print "CSV ROI ID Number not valid"

        # initially create the object with an empty list
        # of masks
        self.masks = []

    def namestring(self):
        name = '{0}_{1}_{2:04d}'.format(self.site, self.roitype,
                                        self.sequence_number)
        return name

    def __unicode__(self):
        return self.namestring()

    def length(self):
        return len(self.masks)

    def readCSV(self, roiListPath):
        """
        Method to read in ROIList from a CSV file and return a
        ROIList object.  If the comment fields are not present
        they must be set before the ROIList can be saved. Should
        get comments from database.
        """

        # open file for read-only access with universal line endings
        f = open(roiListPath, 'rU')

        # get comment lines
        comments = list(_get_comments(f))

        # no validation applied to sitename
        site = _get_comment_field(comments, 'Site')
        if site != "":
            self.site = site

        # roitype should be one of types defined in config.py
        roitype = _get_comment_field(comments, 'Veg Type')
        if roitype != "":
            try:
                config.ROITypes.index(roitype)
                self.roitype = roitype
            except ValueError:
                print "Unknown Veg Type in CSV"

        # sequence number should be decimal
        sequence_number = _get_comment_field(comments, 'ROI ID Number')
        if sequence_number != "":
            try:
                self.sequence_number = int(sequence_number)
            except ValueError:
                print "CSV ROI ID Number not valid"

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

        # no validation for owner
        self.owner = _get_comment_field(comments, 'Owner')

        # no validation for Description
        self.descrip = _get_comment_field(comments, 'Description')

        # get mask rows
        f.seek(0)
        csvrdr = csv.DictReader(_filter_comments(f))

        roimaskList = []
        for row in csvrdr:

            roi_row = {}

            # turn date and time strings into datetime values
            (start_yr, start_mo, start_dom) = row['start_date'].split('-')
            (start_hr, start_min, start_sec) = row['start_time'].split(':')
            start_dt = datetime(int(start_yr), int(start_mo), int(start_dom),
                                int(start_hr), int(start_min), int(start_sec))

            (end_yr, end_mo, end_dom) = row['end_date'].split('-')
            (end_hr, end_min, end_sec) = row['end_time'].split(':')
            end_dt = datetime(int(end_yr), int(end_mo), int(end_dom),
                              int(end_hr), int(end_min), int(end_sec))

            roi_row['start_dt'] = start_dt
            roi_row['end_dt'] = end_dt
            roi_row['maskfile'] = row['maskfile']
            roi_row['sample_image'] = row['sample_image']

            roimaskList.append(roi_row)

        f.close()

        self.masks = roimaskList

    def writeCSV(self, file=""):
        """
        Method for writing ROIList to CSV file.  The method
        opens the file, filename, for writing.  If no file object is passed
        write to stdout instead.

        Do we need to be careful to avoid overwriting an existing
        file?  Yes!
        """

        if file == "":
            fo = sys.stdout
        else:
            fo = open(file, 'w')

        # Before we do anything, check to make sure the roilist object
        # if valid.  Other tests?  Check for valid user?  Warning/Error if
        # no description?
        errlist = self.checkTimes()
        if len(errlist) > 0:
            sys.stderr.write("Invalid start/end times in ROI list.\n")
            sys.exit(1)

        # write header
        hdstrings = []
        hdstrings.append('#\n')
        hdstrings.append('# ROI List for {0}\n'.format(self.site))
        hdstrings.append('#\n')
        hdstrings.append('# Site: {0}\n'.format(self.site))
        hdstrings.append('# Veg Type: {0}\n'.format(self.roitype))
        hdstrings.append('# ROI ID Number: {0:04d}\n'.format(
            self.sequence_number))
        hdstrings.append('# Owner: {0}\n'.format(self.owner))
        hdstrings.append('# Creation Date: {0}\n'.format(
            self.created_at.date()))
        create_time = self.created_at.time()
        hdstrings.append(
            '# Creation Time: {0:02d}:{1:02d}:{2:02d}\n'.format(
                create_time.hour,
                create_time.minute,
                create_time.second))
        hdstrings.append('# Update Date: {0}\n'.format(
            self.updated_at.date()))

        # set update time to now
        self.updated_at = datetime.now()
        update_time = self.updated_at.time()
        hdstrings.append(
            '# Update Time: {0:02d}:{1:02d}:{2:02d}\n'.format(
                update_time.hour,
                update_time.minute,
                update_time.second))
        hdstrings.append('# Description: {0}\n'.format(self.descrip))
        hdstrings.append('#\n')

        for line in hdstrings:
            fo.write(line)

        # print fields line
        fo.write("start_date,start_time,end_date,end_time,maskfile," +
                 "sample_image\n")

        for mask in self.masks:
            start_date = mask['start_dt'].date()
            start_time = mask['start_dt'].time()
            end_date = mask['end_dt'].date()
            end_time = mask['end_dt'].time()
            fo.write("{0},{1},{2},{3},{4},{5}\n".format(start_date,
                                                        start_time,
                                                        end_date,
                                                        end_time,
                                                        mask['maskfile'],
                                                        mask['sample_image']))
        # close output
        if not file == "":
            fo.close()

    def checkTimes(self):
        """
        make sure that for the mask entry N:

        start_dt(N) >= end_dt(N-1)
        end_dt(N) > start_dt(N)

        """
        error_list = []
        lastmask = {}
        for imask, mask in enumerate(self.masks):
            if mask['end_dt'] <= mask['start_dt']:
                error_list.append({'valid': False,
                                   'mask': imask + 1,
                                   'msg':
                                   'End date-time is before start datetime'})

            if imask > 0:
                if mask['start_dt'] < lastmask['end_dt']:
                    error_list.append({'valid': False,
                                       'mask': imask + 1,
                                       'msg': 'Overlaps previous mask.'})

            lastmask = mask

        return(error_list)
