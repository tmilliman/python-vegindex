============
Installation
============

The initial version of the package only works with Python2 and
has only been tested on version 2.7.  A Python3 version should
be available soon.  The package had limited testing on linux, OSX
and Windows.

Virtual Environments
--------------------

The ``vegindex`` package has typically been used in a virtual environment.
For Python2 this means installing ``virtualenv`` (and optionally
``virtualenvwrapper``) or ``pyenv``.  I have also used
`Anaconda/Miniconda <https://www.continuum.io>`_ which has it's own virtual
environment manager.  The use of virtual environments is
beyond the scope of this document but using them is highly recommended.

When using ``virtulalenvwrapper``:

::

   mkvirtualenv vegindex


This both creates and activates the virtualenv wrapper.  After that
Hopefully, installation will be as simple as installing the package:
At the command line::

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
