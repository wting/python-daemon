# -*- coding: utf-8 -*-

# daemon/_metadata.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Package metadata for the ‘python-daemon’ distribution. """

from __future__ import (absolute_import, unicode_literals)

import os
import os.path
import json
import datetime

try:
    # Python 2 has both ‘str’ (bytes) and ‘unicode’.
    basestring = basestring
    unicode = unicode
except NameError:
    # Python 3 names the Unicode data type ‘str’.
    basestring = str
    unicode = str

import pkg_resources


version_info_file_path = os.path.join(
        os.path.dirname(__file__), "version_info.json")

def read_version_info_from_file(file_path):
    """ Read the version info from the specified file.

        :param file_path: Filesystem path to the version info file.
        :return: The version info mapping.

        The version info file is a JSON-serialised mapping of
        information about the VCS revision from which the source tree
        was built.

        """
    infile = open(file_path, 'rt')
    info_raw = json.load(infile)

    item_converters = {}

    info = {}
    for (name, value_raw) in info_raw.items():
        if name in item_converters:
            value = item_converters[name](value_raw)
        else:
            value = value_raw
        info[name] = value

    return info


distribution_name = "python-daemon"

def get_distribution_version():
    """ Get the version from the installed distribution. """
    try:
        distribution = pkg_resources.get_distribution(distribution_name)
    except pkg_resources.DistributionNotFound:
        distribution = None

    version = None
    if distribution is not None:
        version = distribution.version

    return version

version_installed = get_distribution_version()

author_name = "Ben Finney"
author_email = "ben+python@benfinney.id.au"
author = "{name} <{email}>".format(name=author_name, email=author_email)


class YearRange:
    """ A range of years spanning a period. """

    def __init__(self, begin, end=None):
        self.begin = begin
        self.end = end

    def __unicode__(self):
        text = "{range.begin:04d}".format(range=self)
        if self.end is not None:
            if self.end > self.begin:
                text = "{range.begin:04d}–{range.end:04d}".format(range=self)
        return text

    __str__ = __unicode__


def make_year_range(begin_year, end_date=None):
    """ Construct the year range given a start and possible end date.

        :param begin_date: The beginning year (text) for the range.
        :param end_date: The end date (text, ISO-8601 format) for the
            range.
        :return: The range of years as a `YearRange` instance.

        If the `end_date` is ``None``, the range has ``None`` for the
        end year.

        """
    begin_year = int(begin_year)

    end_year = None
    if end_date is not None:
        end_year_text = end_date.split('-')[0]
        end_year = int(end_year_text)

    year_range = YearRange(begin=begin_year, end=end_year)

    return year_range

version_info = read_version_info_from_file(version_info_file_path)

copyright_year_begin = "2001"
build_date = version_info['released'].split(' ', 1)[0]
copyright_year = build_date.split('-')[0]
copyright_year_range = make_year_range(copyright_year_begin, build_date)

copyright = "Copyright © {year_range} {author} and others".format(
        year_range=copyright_year_range, author=author)
license = "Apache-2"
url = "https://alioth.debian.org/projects/python-daemon/"


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
