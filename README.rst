========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
    * - package
      - | |version|
      - | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-vegindex/badge/?style=flat
    :target: https://readthedocs.org/projects/python-vegindex
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/tmilliman/python-vegindex.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/tmilliman/python-vegindex

.. |version| image:: https://img.shields.io/pypi/v/vegindex.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/vegindex

.. |commits-since| image:: https://img.shields.io/github/commits-since/tmilliman/python-vegindex/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/tmilliman/python-vegindex/compare/v0.1.0...master

.. end-badges

Python tools for generating vegetation index timeseries from PhenoCam images.

* Free software: BSD license

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
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
