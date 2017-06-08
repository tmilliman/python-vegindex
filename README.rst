========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - | |docs|

    * - tests
      - | |travis|

    * - package
      - | |version|

.. |docs| image:: https://readthedocs.org/projects/python-vegindex/badge/?style=flat
    :target: https://readthedocs.org/projects/python-vegindex
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/tmilliman/python-vegindex.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/tmilliman/python-vegindex

.. |version| image:: https://img.shields.io/pypi/v/vegindex.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/vegindex

.. end-badges

Python tools for generating vegetation index timeseries from PhenoCam images.

* Free software: MIT license

Installation
============

::

    pip install vegindex

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
