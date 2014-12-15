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
    infile = open(file_path, 'r')
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
try:
    distribution = pkg_resources.get_distribution(distribution_name)
except pkg_resources.DistributionNotFound:
    distribution = None

version_installed = None
if distribution is not None:
    version_installed = distribution.version

author_name = "Ben Finney"
author_email = "ben+python@benfinney.id.au"
author = "%(author_name)s <%(author_email)s>" % vars()

version_info = read_version_info_from_file(version_info_file_path)
copyright_year_begin = "2001"
date = version_info['date'].split(' ', 1)[0]
copyright_year = date.split('-')[0]
copyright_year_range = copyright_year_begin
if copyright_year > copyright_year_begin:
    copyright_year_range += "–%(copyright_year)s" % vars()

copyright = (
        "Copyright © %(copyright_year_range)s %(author)s and others"
        ) % vars()
license = "Apache-2"
url = "https://alioth.debian.org/projects/python-daemon/"


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
