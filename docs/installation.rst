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
For Python2 this means installing ``virtualenv`` (and optionally
``virtualenvwrapper``) or ``pyenv``.  I have also used
`Anaconda/Miniconda <https://www.anaconda.com>`_ which has it's own virtual
environment manager.  The use of virtual environments is
beyond the scope of this document but using them is highly recommended.

When using ``virtulalenvwrapper``:

::

   mkvirtualenv vegindex


This both creates and activates the virtualenv wrapper.  After that
Hopefully, installation will be as simple as installing the package:
At the command line:

::

    pip install vegindex


The package does however depend on other packages, most
notably ``PIL/pillow``, ``numpy`` and ``pyephem`` which may need to be
installed separately on your platform.  In particular installing
``PIL/pillow`` seems to cause problems and not work automatically.  If
you have a modern version of ``pip`` installed you can often just
do the following:

::

   pip install Pillow
   pip install vegindex


Current versions of pip allow you to specify the python version and
can be used with python3.

If you will be using Python 3 then you already have ``pyvenv`` installed
and can use that to create your virtual environment.  


python3 -m venv vegindex3
source vegindex3/bin/activate


Platform Notes
--------------

OSX
^^^
TBD

Linux
^^^^^
TBD

Windows
^^^^^^^
TBD
