#!/usr/bin/env python

"""
Utility functions for accessing image archive.
"""

import os
import re
import sys
from datetime import datetime
from datetime import timedelta

import ephem
import requests

from . import config

# ####################################################################


def fn2date(sitename, filename, irFlag=False):
    """
    Function to extract the date from a "standard" filename based on a
    sitename.  Here we assume the filename format is the standard:

          sitename_YYYY_MM_DD_HHNNSS.jpg

    So we just grab components from fixed positions.  If irFlag is
    True then the "standard" format is:

          sitename_IR_YYYY_MM_DD_HHNNSS.jpg

    """

    if irFlag:
        prefix = sitename + "_IR"
    else:
        prefix = sitename

    # set start of datetime part of name
    nstart = len(prefix) + 1

    # assume 3-letter extension e.g. ".jpg"
    dtstring = filename[nstart:-4]

    # extract date-time pieces
    year = int(dtstring[0:4])
    mon = int(dtstring[5:7])
    day = int(dtstring[8:10])
    hour = int(dtstring[11:13])
    mins = int(dtstring[13:15])
    sec = int(dtstring[15:17])

    # return list
    return [year, mon, day, hour, mins, sec]

# ####################################################################


def fn2datetime(sitename, filename, irFlag=False):
    """
    Function to extract the date from a "standard" filename based on a
    sitename.  Here we assume the filename format is the standard:

          sitename_YYYY_MM_DD_HHNNSS.jpg

    So we just grab components from fixed positions.  If irFlag is
    True then the "standard" format is:

          sitename_IR_YYYY_MM_DD_HHNNSS.jpg

    """

    if irFlag:
        prefix = sitename + "_IR"
    else:
        prefix = sitename

    # set start of datetime part of name
    nstart = len(prefix) + 1

    # assume 3-letter extension e.g. ".jpg"
    dtstring = filename[nstart:-4]

    # extract date-time pieces
    year = int(dtstring[0:4])
    mon = int(dtstring[5:7])
    day = int(dtstring[8:10])
    hour = int(dtstring[11:13])
    mins = int(dtstring[13:15])
    sec = int(dtstring[15:17])

    # return list
    return datetime(year, mon, day, hour, mins, sec)

# ####################################################################


def getsiteimglist(sitename,
                   startDT=datetime(1990, 1, 1, 0, 0, 0),
                   endDT=datetime.now(),
                   getIR=False):
    """
    Returns a list of imagepath names for ALL images in
    archive for specified site.  Optional arguments:
      getIR   : If set to true only return IR images.
      startDT : Start datetime for image list
      endDT   : End datetime for image list

    NOTE: This might be lots faster if we just do a glob.glob()
    on a pattern.  Might not be quite as robust since we're skipping
    the check the .jpg file being a regular file.  See, getImageCount()
    below for how this would work!
    """

    # get startyear and endyear
    startYear = startDT.year
    endYear = endDT.year

    # get startmonth and endmonth
    startMonth = startDT.month
    endMonth = endDT.month

    imglist = []
    sitepath = os.path.join(config.archive_dir, sitename)
    if not os.path.exists(sitepath):
        return imglist

    # get a list of files in the directory
    yeardirs = os.listdir(sitepath)

    # loop over all files
    for yeardir in yeardirs:

        # check that its a directory
        yearpath = os.path.join(sitepath, yeardir)
        if not os.path.isdir(yearpath):
            continue

        # check if this yeardir could be a 4-digit year.  if not skip
        if not re.match('^\d\d\d\d$', yeardir):
            continue

        # check if we're before startYear
        if (int(yeardir) < startYear) | (int(yeardir) > endYear):
            continue

        # get a list of all files in year directory
        mondirs = os.listdir(yearpath)

        # loop over all files
        for mondir in mondirs:

            # check that its a directory
            monpath = os.path.join(yearpath, mondir)
            if not os.path.isdir(monpath):
                continue

            # check if this mondir could be a 2-digit month.  if not skip
            if not re.match('^\d\d$', mondir):
                continue

            # check month range
            if (int(mondir) < 1) | (int(mondir) > 12):
                continue

            # check start year/month
            if (int(yeardir) == startYear) & (int(mondir) < startMonth):
                continue

            # check end year/month
            if (int(yeardir) == endYear) & (int(mondir) > endMonth):
                continue

            try:
                imgfiles = os.listdir(monpath)
                if getIR:
                    image_re = "^%s_IR_%s_%s_.*\.jpg$" % (
                        sitename, yeardir, mondir)
                else:
                    image_re = "^%s_%s_%s_.*\.jpg$" % (
                        sitename, yeardir, mondir)

                for imgfile in imgfiles:
                    # check for pattern match
                    if not re.match(image_re, imgfile):
                        continue

                    # get image time
                    [yr, mo, md, hr, mn, sc] = fn2date(
                        sitename, imgfile, irFlag=getIR)
                    img_dt = datetime(yr, mo, md, hr, mn, sc)

                    if img_dt < startDT:
                        continue

                    if img_dt > endDT:
                        continue

                    # only add regular files
                    imgpath = os.path.join(monpath, imgfile)
                    if not os.path.isdir(imgpath):
                        imglist.append(imgpath)

            except OSError as e:
                if e.errno == 20:
                    continue
                else:
                    errstring = "Python OSError: %s" % (e,)
                    print(errstring)

    imglist.sort()
    return imglist

# ####################################################################


def getsiteinfo(sitename):
    """
    Simple function to return the site info for a single site in a dictionary
    by grabbing JSON from a URL.
    """

    siteinfo = {}
    try:
        infourl = "https://phenocam.sr.unh.edu/webcam/" + \
                  "sites/{0}/info/".format(sitename)
        response = requests.get(infourl)
    except:
        sys.stderr.write("Error getting site info.\n")
        return None

    siteinfo = response.json()
    return siteinfo

# ####################################################################


def deg2dms(angle):
    """
    helper function to convert angle in fractional
    degrees to a string of the form dd:mm:ss
    """
    deg = int(angle)
    degdiff = abs(angle - float(deg))
    minangle = degdiff * 60.
    min = int(minangle)
    mindiff = minangle - float(min)
    sec = int(mindiff * 60.)
    dmsstr = "{0:02d}:{1:02d}:{2:02d}".format(deg, min, sec)
    return dmsstr

# ####################################################################


def dms2deg(dmsstr):
    """
    convert dms string in form 'dd:mm:ss' to fractional degrees.
    """
    (dd, mm, ss) = dmsstr.split(':')
    degrees = dd + mm * 1. / 60. + ss * 1. / 3600.
    return degrees

# ####################################################################


def sunelev(lat, lon, dt, tzoffset):
    """
    function to return the solar elevation at a given
    latitude (decimal degrees) and longitude (decimal degrees)
    and local date and time.  The time is assumed to be
    the local "standard" time and the offset is the rawOffset
    from UTC/GMT (i.e. the offset for "standard time").
    """

    # set up observer for ephem package
    site = ephem.Observer()
    site.lat = deg2dms(lat)
    site.lon = deg2dms(lon)

    # apply timezone offset to local time to give
    # utc time
    utcdt = dt + timedelta(hours=-tzoffset)
    site.date = utcdt

    # get sun position
    sun = ephem.Sun(site)

    # return elevation is decimal degrees
    elev = sun.alt / ephem.degree

    return elev
