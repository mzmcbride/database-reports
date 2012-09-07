# -*- coding: utf-8 -*-
"""
MediaWiki database reports

"""
from setuptools import setup, find_packages



setup(
    name='dbreports',
    packages=find_packages(),
    version='0.1-dev',
    url='https://en.wikipedia.org/wiki/Wikipedia:Database_reports',
    description='MediaWiki database reports',
    author='MZMcBride',
    email="z@mzmcbride.com",
    long_description=__doc__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: Public Domain',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ]
)
