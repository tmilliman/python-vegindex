# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ).read()


setup(
    name="vegindex",
    version="0.10.2",
    license="MIT",
    description="Python tools for generating vegetation index timeseries from PhenoCam images.",
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    long_description_content_type="text/x-rst",
    author="Thomas Milliman",
    author_email="thomas.milliman@unh.edu",
    url="https://github.com/tmilliman/python-vegindex/",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    keywords=["phenology", "phenocam", "vegetation", "index"],
    install_requires=[
        "matplotlib",
        "Pillow",
        "pyephem",
        "requests",
        "numpy",
        "pandas",
    ],
    extras_require={"rst": ["docutils"]},
    entry_points={
        "console_scripts": [
            "generate_roi_timeseries=vegindex.generate_roi_timeseries:main",
            "update_roi_timeseries=vegindex.update_roi_timeseries:main",
            "generate_roi_ir_timeseries=vegindex.generate_roi_ir_timeseries:main",
            "update_roi_ir_timeseries=vegindex.update_roi_ir_timeseries:main",
            "generate_summary_timeseries=vegindex.generate_summary_timeseries:main",
            "update_summary_timeseries=vegindex.update_summary_timeseries:main",
            "generate_ndvi_timeseries=vegindex.generate_ndvi_timeseries:main",
            "generate_ndvi_summary_timeseries=vegindex.generate_ndvi_summary_timeseries:main",
            "update_ndvi_summary_timeseries=vegindex.update_ndvi_summary_timeseries:main",
            "plot_roistats=vegindex.plot_roistats:main",
        ]
    },
)
