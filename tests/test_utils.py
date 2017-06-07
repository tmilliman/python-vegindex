# -*- coding: utf-8 -*-

"""
Tests for `vegindex.utils` module.
"""

from vegindex import utils


def test_get_siteinfo():
    """
    get getting site info from URL
    """

    sitename = 'harvard'
    siteinfo = utils.getsiteinfo(sitename)

    assert siteinfo['lon'] == -72.1715
