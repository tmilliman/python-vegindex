Changelog
=========
0.7.2 (2030-04-12)
------------------
* Add 3.8 tox environment to tox.ini

0.7.0 (2020-04-01)
------------------
* Add checks when reading an ROI List CSV file that the
  time ranges are in order and don't overlap

0.6.1 (2019-07-15)
------------------
* Update installation doc.
* Simple test for reading roistats file.

0.6.0 (2019-07-12)
------------------
* Add awbflag (auto white-balance) to roistats file

0.5.3 (2019-04-03)
------------------
* Update requirements for python 3.7
* Add prefix to regular expressions

0.5.2 (2018-04-09)
------------------
* Really fix bug in plot_roistats when no data are filtered.

0.5.1 (2018-04-09)
------------------
* Fix bug in plot_roistats when no data are filtered.
* Update docs

0.5.0 (2017-11-29)
--------------------
* Fix header on roistats.csv file
* Add plotting script (matplotlib library is now required)
* Remove timeout on requests query which was causing
  tests to fail.
* Update usage docs

0.4.0 (2017-11-27)
--------------------
* Add fallback to local site_info.csv file to get basic site metadata
* Update exception handling (removed bare exceptions)

0.3.1 (2017-10-06)
---------------------
* Change data product name from _roi_statistics.csv to _roistats.csv

0.3.0 (2017-09-12)
---------------------
* Added support for .meta files
* Change data product name from _timeseries.csv to _roi_statistics.csv

0.2.0rc1 (2017-06-14)
---------------------
* Added support for python3

0.1.1rc3 (2017-06-13)
----------------------
* First release on PyPI.
