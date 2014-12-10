# -*- coding: utf-8 -*-
#
# test/__init__.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2012 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file LICENSE.ASF-2 for details.

""" Unit test suite for ‘daemon’ package.
    """

from __future__ import unicode_literals

import scaffold


suite = scaffold.make_suite()
