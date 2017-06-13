=====
Usage
=====


Command Line Scripts
--------------------

After installing the ``vegindex`` package, two python command line
scripts will be installed:

* ``generate_roi_timeseries``
* ``generate_summary_timeseries``

The first script generates summary statistics for a Region of Interest
(ROI) for each image which passes certain basic selection criteria and
writes the results to a file.  The second script reads in this file
and then calculates either 1-day or 3-day summaries statistics for all
the images in this period.

Setting up the Data Directory
-----------------------------

The vegindex package is designed to work with images downloaded from
the PhenoCam network server.  To download images you can go to our
`data page <https://phenocam.sr.unh.edu/webcam/network/download/>`_.

The images you select come in a zip file with a specific directory
structure.  For example if we download data from the ``harvard`` site.

::

   harvard
   ├── 2009
   │   ├── 01
   │   │   ├── harvard_2009_01_01_110135.jpg
   │   │   ├── harvard_2009_01_01_113135.jpg
   │   │   ├── harvard_2009_01_01_120135.jpg
    .
    .
    .

   │   └── 06
   │       ├── harvard_2009_06_01_110139.jpg
   │       ├── harvard_2009_06_01_113139.jpg
   │       ├── harvard_2009_06_01_120139.jpg
   │       └── harvard_2009_06_01_123139.jpg
   ├── harvard_meta.json
   └── harvard_meta.txt

where the we have a top level directory for ``sitename`` then
subdirectories for year and month, with the image files in the
month directories.


ROI Lists and Masks
-------------------

Once you've selected and downloaded the data you would like to process
you will need to set up a region of interest (ROI) using an ``ROI List``
file and the associated ``ROI Mask`` images.

The ``ROI List`` file is a simple text file with
a list of ``ROI mask`` images and the dates for which the masks are
valid.  The ``ROI List`` format description can be found
on this `page <https://phenocam.sr.unh.edu/webcam/tools/roi_list_format/>`_
Here's a simple example where there is only one mask file:

::

   #
   # ROI List for harvard
   #
   # Site: harvard
   # Veg Type: DB
   # ROI ID Number: 0001
   # Owner: tmilliman
   # Creation Date: 2012-07-12
   # Creation Time: 11:42:00
   # Update Date: 2014-12-17
   # Update Time: 13:55:25
   # Description: Deciduous trees in foreground
   #
   start_date,start_time,end_date,end_time,maskfile,sample_image
   2008-04-04,00:00:00,9999-01-01,00:00:00,harvard_DB_0001_01.tif,harvard_2008_04_30_133137.jpg


If there are field-of-view shifts you may need additional lines in the
list and more mask images.  The list file and the mask images need to be
placed in a directory named ``ROI`` under the site name i.e.:

::

   harvard
   └── ROI
       ├── harvard_DB_0001_01.tif
       └── harvard_DB_0001_roi.csv


This file naming convention must also be followed.  So the ``ROI List``
has the form:

::

   <sitename>_<ROI-type>_<ROI-sequence-no>_roi.csv

and the associated masks are named according to the convention:

::

   <sitename>_<ROI-type>_<ROI-sequence-no>_<mask_index>.tif

where the "<mask_index>" in the form ``nn`` is the number in the list
of the mask file starting with 01 (e.g. 01, 02, 03, etc.).  For the
timeseries displayed on the PhenoCam Network website.  The ``ROI
List`` files and the ``ROI Mask`` images are available for download
from one of the ``ROI Pages`` on our site e.g.  `ROI page for harvard
DB_0001
<https://phenocam.sr.unh.edu/data/archive/harvard/ROI/harvard_DB_0001.html>`_


Generating the "All-image" file
-------------------------------

The ``generate_roi_timeseries`` script reads in the ``ROI List``
file and ``ROI Mask`` images. Then for each image found within the
timeperiods in the ``ROI List`` it calculates image statistics over
the ROI.  You can get help for

::

   $ generate_roi_timeseries -h
   usage: generate_roi_timeseries [-h] [-v] [-n] site roiname

   positional arguments:
   site           PhenoCam site name
   roiname        ROI name, e.g. DB_0001

   optional arguments:
   -h, --help     show this help message and exit
   -v, --verbose  increase output verbosity
   -n, --dry-run  Process data but don't save results


The script needs to know where the site images are located.  By default
it assumes that the site level image directory is at:
::

   /data/archive/<sitename>

If the images downloaded are in another location, for example
``/mydata/directory/harvard``, you can set an an
environment variable to specify the path to the images:
::

   export PHENOCAM_ARCHIVE_DIR=/mydata/directory/

or

::

   set PHENOCAM_ARCHIVE_DIR=/mydata/directory/


Here's an example command line session:
::

   $ export PHENOCAM_ARCHIVE_DIR=~/Downloads/phenocamdata/
   $ generate_roi_timeseries harvard DB_0001
   Images processed: 594
   Images added to CSV: 594
   Total: 594


The output format for the "All Image" file can be found
`here <https://phenocam.sr.unh.edu/webcam/tools/roi_timeseries_format/>`_

Generating the 1-day and 3-day Summary Files
--------------------------------------------

The ``generate_summary_timeseries`` script reads in the "All-Image"
file and calculates summary statistics for the 1-day or 3-day period:

::

   $ generate_summary_timeseries -h
   usage: generate_summary_timeseries [-h] [-v] [-n] [-p [{1,3}]] site roiname

   positional arguments:
   site                  PhenoCam site name
   roiname               ROI name, e.g. canopy_0001

   optional arguments:
   -h, --help            show this help message and exit
   -v, --verbose         increase output verbosity
   -n, --dry-run         Process data but don't save results
   -p [{1,3}], --aggregation-period [{1,3}]
                         Number of Days to Aggregate (default=1)

To generate the 3-day summary file from the "All Image" file generated
in the previous section:

::

   $ generate_summary_timeseries -p 3 harvard DB_0001
   Total: 51

A `description of the summary files <https://phenocam.sr.unh.edu/webcam/tools/gcc_file_format/>`_
can be found on the project website.

API
---

TBD
