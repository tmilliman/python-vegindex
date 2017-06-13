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
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='vegindex',
    version='0.1.1rc3',
    license='MIT',
    description='Python tools for generating vegetation index timeseries from PhenoCam images.',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges',
                   re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author='Thomas Milliman',
    author_email='thomas.milliman@unh.edu',
    url='https://github.com/tmilliman/python-vegindex',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: Implementation :: CPython',
        # 'Programming Language :: Python :: Implementation :: PyPy',
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    keywords=[
        'phenology', 'phenocam', 'vegetation', 'index'
    ],
    install_requires=[
        'pillow>=4.0',
        'pyephem>=3.7',
        'configparser>=3.5.0',
        'requests>=2.17.3',
        'numpy==1.13.0',
    ],
    extras_require={
        # eg:
        'rst': ['docutils>=0.11'],
        # ':python_version=="2.6"': ['argparse'],
    },
    entry_points={
        'console_scripts': [
            'generate_roi_timeseries=vegindex.generate_roi_timeseries:main',
            'generate_summary_timeseries=vegindex.generate_summary_timeseries:main'
        ]
    },
)
