# -*- coding: utf-8 -*-

# setup.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
# Copyright © 2008 Robert Niederreiter, Jens Klein
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3 of that license or any later version.
# No warranty expressed or implied. See the file LICENSE.GPL-3 for details.

""" Distribution setup for ‘python-daemon’ library.
    """

from __future__ import unicode_literals

import os
import os.path
import pydoc

from setuptools import setup, find_packages


distribution_name = "python-daemon"
main_module_name = 'daemon'
main_module = __import__(main_module_name, fromlist=[b'_metadata'])
metadata = main_module._metadata

synopsis, long_description = pydoc.splitdoc(
        pydoc.getdoc(main_module))

setup_dir = os.path.dirname(__file__)
version_string_filename = "VERSION"
version_string_file = open(
        os.path.join(setup_dir, version_string_filename), 'r')
version_string = version_string_file.read().strip()


setup(
        name=distribution_name,
        version=version_string,
        packages=find_packages(exclude=["test"]),

        # Setuptools metadata.
        zip_safe=False,
        test_suite="test.suite",
        tests_require=[
            "testtools",
            "testscenarios",
            "MiniMock >=1.2.2",
            ],
        install_requires=[
            "setuptools",
            "lockfile >=0.7,<0.9",
            ],

        # PyPI metadata.
        author=metadata.author_name,
        author_email=metadata.author_email,
        description=synopsis,
        license=metadata.license,
        keywords="daemon fork unix".split(),
        url=metadata.url,
        long_description=long_description,
        classifiers=[
            # Reference: http://pypi.python.org/pypi?%3Aaction=list_classifiers
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: POSIX",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries :: Python Modules",
            ],
        )


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
