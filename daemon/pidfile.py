# -*- coding: utf-8 -*-

# daemon/pidfile.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file LICENSE.ASF-2 for details.

""" Lockfile behaviour implemented via Unix PID files.
    """

from __future__ import (absolute_import, unicode_literals)

from lockfile.pidlockfile import PIDLockFile


class TimeoutPIDLockFile(PIDLockFile, object):
    """ Lockfile with default timeout, implemented as a Unix PID file.

        This uses the ``PIDLockFile`` implementation, with the
        following changes:

        * The `acquire_timeout` parameter to the initialiser will be
          used as the default `timeout` parameter for the `acquire`
          method.

        """

    def __init__(self, path, acquire_timeout=None, *args, **kwargs):
        """ Set up the parameters of a TimeoutPIDLockFile. """
        self.acquire_timeout = acquire_timeout
        super(TimeoutPIDLockFile, self).__init__(path, *args, **kwargs)

    def acquire(self, timeout=None, *args, **kwargs):
        """ Acquire the lock. """
        if timeout is None:
            timeout = self.acquire_timeout
        super(TimeoutPIDLockFile, self).acquire(timeout, *args, **kwargs)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
