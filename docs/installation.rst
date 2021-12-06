============
Installation
============

The current version of the package works with either Python2 or
Python 3.  The primary use and testing of the package has
been done on a Debian linux system. The package had limited
testing on OSX and Windows.

Virtual Environments
--------------------

The ``vegindex`` package has typically been used in a virtual environment.
For Python3 this means having the ``venv`` package installed.
I have also used `Anaconda/Miniconda <https://www.anaconda.com>`_ which has it's own virtual
environment manager.  The use of virtual environments is
beyond the scope of this document but using them is highly recommended.

Python ``venv`` package
-----------------------

When using the ``venv`` package:

::

   mkdir vegindex
   cd vegindex
   python3 -m venv venv
   . venv/bin/activate


After that, hopefully, the installation will be as simple as
installing the package: into the virtual environment.
At the command line:

::

    pip install vegindex

If you have problems please contact the author or submit a problem
report on the `github page`__.

:: _`github page` https://github.com/tmilliman/python-vegindex


Using conda/miniconda environments
----------------------------------

The steps for using this package in a ``conda`` environment are

::

    conda create --name vegindex python=3.9
    conda activate vegindex
    conda install numpy matplotlib pillow requests pandas pyephem
    pip install vegindex


With ``pipenv`` you can do the following in your working directory:

::

   pipenv shell
   pipenv install vegindex
