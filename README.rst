========
vegindex
========

.. image:: https://img.shields.io/pypi/v/vegindex.svg
       :alt: PyPI Package latest release
       :target: https://pypi.python.org/pypi/vegindex

.. image:: https://img.shields.io/travis/tmilliman/python-vegindex.svg
       :alt: Travis-CI Build Status
       :target: https://travis-ci.org/tmilliman/python-vegindex

.. image:: https://readthedocs.org/projects/python-vegindex/badge/?version=latest
       :target: https://python-vegindex.readthedocs.io/en/latest/?badge=latest
       :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/vegindex.svg
       :target: https://pypi.python.org/pypi/vegindex
       :alt: Supported versions

Python tools for generating vegetation index timeseries from PhenoCam images.

* Free software: MIT license

Introduction
============

The PhenoCam Network is a project designed to study the patterns of
seasonal variation (phenology) of vegetation.  The project website is
at `https://phenocam.sr.unh.edu/ <https://phenocam.sr.unh.edu/webcam/>`_.  The
network consists of many cameras collecting images of various types of
vegetation.  By analysing the images we can quantify the seasonal
changes at a particular camera site.

A "vegetation index" refers to a quantity calculated using information
from various spectral bands of an image of a vegetated area.  The image is
typically obtained from a remote-sensing instrument on an earth
orbiting satellite. There are several vegetation index values in
common usage.  The most widely used are NDVI (Normalized Difference
Vegetation Index) and EVI (Enhanced Vegetation Index).  For the PhenoCam
project the Green Chromatic Coordinate or GCC is our standard vegetation
index.

For the PhenoCam network, the images are obtained from webcams (usually
installed on towers) looking across a vegetated landscape.  These
images are typically in JPEG format and have 3-bands (Red, Green, and
Blue).  For some cameras a separate image dominated by an IR (infrared)
band is collected.

The algorithms used in in this package have been discussed in numerous
publications.  You can find a list of publications for the PhenoCam
Network project `here <https://phenocam.sr.unh.edu/webcam/publications/>`_.
The details of the calculation of GCC are presented in this
`python notebook <https://github.com/tmilliman/phenocam_notebooks/blob/master/Standard_Processing_ROI_Stats/PhenoCam_ROI_stats.ipynb>`_
.

..
   Richardson, A.D., Hufkens, K., Milliman, T., Aubrecht, D.M.,
   Chen, M., Gray, J.M., Johnston, M.R., Keenan, T.F., Klosterman,
   S.T., Kosmala, M., Melaas, E.K., Friedl, M.A., Frolking, S. 2017.
   Vegetation Phenology from PhenoCam v1.0. ORNL DAAC, Oak Ridge, Tennessee,
   USA. https://doi.org/10.3334/ORNLDAAC/1358


After the package is installed two python scripts should be available:

* ``generate_roi_timeseries``
* ``generate_summary_timeseries``

These scripts allow you to reproduce the PhenoCam network
"standard timeseries products" from downloaded data.  For a description
of the products see the project
`Tools Page <https://phenocam.sr.unh.edu/webcam/tools/>`_.


Quick Installation
==================

From the command line type:

::

   pip install vegindex


Some of the packages that ``vegindex`` depends on may not install
automatically (using ``pip``) since they depend on system libraries.
If the above command does not work you can try:

::

   pip install Pillow
   pip install vegindex


The latest version of the documentation can be found at
`readthedocs.io <https://python-vegindex.readthedocs.io/en/latest/>`_
