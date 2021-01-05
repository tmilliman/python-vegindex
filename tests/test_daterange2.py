# -*- coding: utf-8 -*-

"""
test_daterange2
---------------

Tests for `vegindex.vegindex.daterange2` module
"""

import os
from datetime import date

import numpy as np

from vegindex import vegindex as vi

end_date = date(2008, 1, 31)

start_date = date(2008, 1, 1)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 1))

start_date = date(2008, 1, 2)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 1))

start_date = date(2008, 1, 3)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 1))

start_date = date(2008, 1, 4)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 4))

start_date = date(2008, 1, 5)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 4))

start_date = date(2008, 1, 6)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 4))

start_date = date(2008, 1, 7)
mydate = next(vi.daterange2(start_date, end_date, 3))
np.testing.assert_equal(mydate, date(2008, 1, 7))
