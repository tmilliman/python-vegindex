========
vegindex
========

.. image:: https://img.shields.io/pypi/v/vegindex.svg
       :alt: PyPI Package latest release
       :target: https://testpypi.python.org/pypi/vegindex

.. image:: https://img.shields.io/travis/tmilliman/vegindex.svg
       :alt: Travis-CI Build Status
       :target: https://travis-ci.org/tmilliman/vegindex

.. image:: https://readthedocs.org/projects/vegindex/badge/?version=latest
       :target: https://vegindex.readthedocs.io/en/latest/?badge=latest
       :alt: Documentation Status


Python tools for generating vegetation index timeseries from PhenoCam images.

* Free software: MIT license

.. image:: images/gcc-values.png

Introduction
============

The PhenoCam Network is a project designed to study the patterns of
seasonal variation (phenology) of vegetation.  The project website is
at `https://phenocam.sr.unh.edu/ <https://phenocam.sr.unh.edu/webcam/>`_.  The
network consists of many cameras collecting images of various types of
vegetation.  By analysing the images we can quantify the seasonal
changes at a particular camera site.

A "vegetation index" refers to quantity calculated using information
from various spectral bands of an image of vegetation.  The image is
typically obtained from a remote-sensing instrument on a earth
orbiting satellite. There are several vegetation index values in
common usage.  The most widely used are NDIV (Normalized Difference
Vegetation Index) and EVI (Enhanced Vegetation Index).  For the PhenoCam
project the GCC (Green Chromatic Coordinate) is our standard vegetation
index.

For the PhenoCam network, the images are obtained from webcams (usually
installed on towers) looking across a vegetated landscape.  These
images are typically in JPEG format and have 3-bands (Red, Green, and
Blue).  For some cameras a separate image dominated by an IR (infrared)
band is collected.

The algorithms used in in this package have been discussed in numerous
publications.  You can find a list of publications for the PhenoCam
Project `here <https://phenocam.sr.unh.edu/webcam/publications/>`_.

Installation
============

The initial version of the package only works with Python2 and
has only been tested on version 2.7.  A Python3 version should
be available soon.

Hopefully, installation will be as simple as installing the package:

::

    pip install vegindex


The package does however depend on other packages packages most
notably ``PIL/pillow``, ``numpy`` and ``pyephem`` which may need to be
install separately on your platform.

Documentation
=============

https://python-vegindex.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 100
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append tox


    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
