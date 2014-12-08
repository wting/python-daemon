# -*- coding: utf-8 -*-
#
# test/test_pidfile.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Unit test for ‘pidfile’ module.
    """

from __future__ import unicode_literals

import os
from StringIO import StringIO
import itertools
import tempfile
import errno

import mock
import lockfile
from lockfile import pidlockfile

import scaffold

from daemon import pidfile


class FakeFileDescriptorStringIO(StringIO, object):
    """ A StringIO class that fakes a file descriptor. """

    _fileno_generator = itertools.count()

    def __init__(self, *args, **kwargs):
        self._fileno = self._fileno_generator.next()
        StringIO.__init__(self, *args, **kwargs)

    def fileno(self):
        return self._fileno

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def make_pidlockfile_scenarios():
    """ Make a collection of scenarios for testing PIDLockFile instances. """

    fake_current_pid = 235
    fake_other_pid = 8642
    fake_pidfile_path = tempfile.mktemp()

    fake_pidfile_empty = FakeFileDescriptorStringIO()
    fake_pidfile_current_pid = FakeFileDescriptorStringIO(
            "%(fake_current_pid)d\n" % vars())
    fake_pidfile_other_pid = FakeFileDescriptorStringIO(
            "%(fake_other_pid)d\n" % vars())
    fake_pidfile_bogus = FakeFileDescriptorStringIO(
            "b0gUs")

    scenarios = {
            'simple': {},
            'not-exist': {
                'open_func_name': 'mock_open_nonexist',
                'os_open_func_name': 'mock_os_open_nonexist',
                },
            'not-exist-write-denied': {
                'open_func_name': 'mock_open_nonexist',
                'os_open_func_name': 'mock_os_open_nonexist',
                },
            'not-exist-write-busy': {
                'open_func_name': 'mock_open_nonexist',
                'os_open_func_name': 'mock_os_open_nonexist',
                },
            'exist-read-denied': {
                'open_func_name': 'mock_open_read_denied',
                'os_open_func_name': 'mock_os_open_read_denied',
                },
            'exist-locked-read-denied': {
                'locking_pid': fake_other_pid,
                'open_func_name': 'mock_open_read_denied',
                'os_open_func_name': 'mock_os_open_read_denied',
                },
            'exist-empty': {},
            'exist-invalid': {
                'pidfile': fake_pidfile_bogus,
                },
            'exist-current-pid': {
                'pidfile': fake_pidfile_current_pid,
                'pidfile_pid': fake_current_pid,
                },
            'exist-current-pid-locked': {
                'pidfile': fake_pidfile_current_pid,
                'pidfile_pid': fake_current_pid,
                'locking_pid': fake_current_pid,
                },
            'exist-other-pid': {
                'pidfile': fake_pidfile_other_pid,
                'pidfile_pid': fake_other_pid,
                },
            'exist-other-pid-locked': {
                'pidfile': fake_pidfile_other_pid,
                'pidfile_pid': fake_other_pid,
                'locking_pid': fake_other_pid,
                },
            }

    for scenario in scenarios.values():
        scenario['pid'] = fake_current_pid
        scenario['pidfile_path'] = fake_pidfile_path
        if 'pidfile' not in scenario:
            scenario['pidfile'] = fake_pidfile_empty
        if 'pidfile_pid' not in scenario:
            scenario['pidfile_pid'] = None
        if 'locking_pid' not in scenario:
            scenario['locking_pid'] = None
        if 'open_func_name' not in scenario:
            scenario['open_func_name'] = 'mock_open_okay'
        if 'os_open_func_name' not in scenario:
            scenario['os_open_func_name'] = 'mock_os_open_okay'

        scenario['pidlockfile_args'] = dict(
                path=scenario['pidfile_path'],
                )
        scenario['test_instance'] = pidlockfile.PIDLockFile(
                **scenario['pidlockfile_args'])

    return scenarios


def setup_pidfile_fixtures(testcase):
    """ Set up common fixtures for PID file test cases. """
    scenarios = make_pidlockfile_scenarios()
    testcase.pidlockfile_scenarios = scenarios

    def get_scenario_option(testcase, key, default=None):
        value = default
        try:
            value = testcase.scenario[key]
        except (NameError, TypeError, AttributeError, KeyError):
            pass
        return value

    func_patcher_os_getpid = mock.patch.object(
            os, "getpid",
            return_value=scenarios['simple']['pid'])
    func_patcher_os_getpid.start()
    testcase.addCleanup(func_patcher_os_getpid.stop)

    def make_fake_open_funcs(testcase):

        def fake_open_nonexist(filename, mode, buffering):
            if 'r' in mode:
                raise IOError(
                        errno.ENOENT, "No such file %(filename)r" % vars())
            else:
                result = testcase.scenario['pidfile']
            return result

        def fake_open_read_denied(filename, mode, buffering):
            if 'r' in mode:
                raise IOError(
                        errno.EPERM, "Read denied on %(filename)r" % vars())
            else:
                result = testcase.scenario['pidfile']
            return result

        def fake_open_okay(filename, mode, buffering):
            result = testcase.scenario['pidfile']
            return result

        def fake_os_open_nonexist(filename, flags, mode):
            if (flags & os.O_CREAT):
                result = testcase.scenario['pidfile'].fileno()
            else:
                raise OSError(
                        errno.ENOENT, "No such file %(filename)r" % vars())
            return result

        def fake_os_open_read_denied(filename, flags, mode):
            if (flags & os.O_CREAT):
                result = testcase.scenario['pidfile'].fileno()
            else:
                raise OSError(
                        errno.EPERM, "Read denied on %(filename)r" % vars())
            return result

        def fake_os_open_okay(filename, flags, mode):
            result = testcase.scenario['pidfile'].fileno()
            return result

        funcs = dict(
                (name, obj) for (name, obj) in vars().items()
                if hasattr(obj, '__call__'))

        return funcs

    testcase.fake_pidfile_open_funcs = make_fake_open_funcs(testcase)

    def fake_open(filename, mode='r', buffering=None):
        scenario_path = get_scenario_option(testcase, 'pidfile_path')
        if filename == scenario_path:
            func_name = testcase.scenario['open_func_name']
            fake_open_func = testcase.fake_pidfile_open_funcs[func_name]
            result = fake_open_func(filename, mode, buffering)
        else:
            result = FakeFileDescriptorStringIO()
        return result

    mock_open = mock.mock_open()
    mock_open.side_effect = fake_open

    func_patcher_builtin_open = mock.patch(
            "__builtin__.open",
            new=mock_open)
    func_patcher_builtin_open.start()
    testcase.addCleanup(func_patcher_builtin_open.stop)

    def fake_os_open(filename, flags, mode=None):
        scenario_path = get_scenario_option(testcase, 'pidfile_path')
        if filename == scenario_path:
            func_name = testcase.scenario['os_open_func_name']
            fake_os_open_func = testcase.fake_pidfile_open_funcs[func_name]
            result = fake_os_open_func(filename, flags, mode)
        else:
            result = FakeFileDescriptorStringIO().fileno()
        return result

    mock_os_open = mock.MagicMock(side_effect=fake_os_open)

    func_patcher_os_open = mock.patch.object(
            os, "open",
            new=mock_os_open)
    func_patcher_os_open.start()
    testcase.addCleanup(func_patcher_os_open.stop)

    def fake_os_fdopen(fd, mode='r', buffering=None):
        scenario_pidfile = get_scenario_option(
                testcase, 'pidfile', FakeFileDescriptorStringIO())
        if fd == testcase.scenario['pidfile'].fileno():
            result = testcase.scenario['pidfile']
        else:
            raise OSError(errno.EBADF, "Bad file descriptor")
        return result

    mock_os_fdopen = mock.MagicMock(side_effect=fake_os_fdopen)

    func_patcher_os_fdopen = mock.patch.object(
            os, "fdopen",
            new=mock_os_fdopen)
    func_patcher_os_fdopen.start()
    testcase.addCleanup(func_patcher_os_fdopen.stop)


def make_lockfile_method_fakes(scenario):
    """ Make common fake methods for lockfile class. """

    def fake_func_read_pid():
        return scenario['pidfile_pid']
    def fake_func_is_locked():
        return (scenario['locking_pid'] is not None)
    def fake_func_i_am_locking():
        return (
                scenario['locking_pid'] == scenario['pid'])
    def fake_func_acquire(timeout=None):
        if scenario['locking_pid'] is not None:
            raise lockfile.AlreadyLocked()
        scenario['locking_pid'] = scenario['pid']
    def fake_func_release():
        if scenario['locking_pid'] is None:
            raise lockfile.NotLocked()
        if scenario['locking_pid'] != scenario['pid']:
            raise lockfile.NotMyLock()
        scenario['locking_pid'] = None
    def fake_func_break_lock():
        scenario['locking_pid'] = None

    fake_methods = dict(
            (
                func_name.replace('fake_func_', ''),
                mock.MagicMock(side_effect=fake_func))
            for (func_name, fake_func) in vars().iteritems()
                if func_name.startswith('fake_func_'))

    return fake_methods


def setup_lockfile_method_mocks(testcase, scenario, class_name):
    """ Set up common mock methods for lockfile class. """
    fake_methods = make_lockfile_method_fakes(scenario)

    for (func_name, fake_func) in fake_methods.iteritems():
        lockfile_func_name = ".".join([class_name, func_name])
        lockfile_func_patcher = mock.patch(
                lockfile_func_name, autospec=True,
                side_effect=fake_func)
        lockfile_func_patcher.start()


def apply_lockfile_method_mocks(mock_lockfile, scenario):
    """ Apply common fake methods to mock lockfile. """
    fake_methods = make_lockfile_method_fakes(scenario)

    for (func_name, fake_func) in fake_methods.iteritems():
        setattr(mock_lockfile, func_name, fake_func)


def setup_pidlockfile_fixtures(testcase, scenario_name=None):
    """ Set up common fixtures for PIDLockFile test cases. """

    setup_pidfile_fixtures(testcase)

    for func_name in [
            'write_pid_to_pidfile',
            'pidlockfile.remove_existing_pidfile',
            ]:
        patcher = mock.patch.object(pidlockfile, func_name)
        patcher.start()
        testcase.addCleanup(patcher.stop)

    if scenario_name is not None:
        set_pidlockfile_scenario(testcase, scenario_name, clear_tracker=False)


def set_pidlockfile_scenario(testcase, scenario_name, clear_tracker=True):
    """ Set up the test case to the specified scenario. """
    testcase.scenario = testcase.pidlockfile_scenarios[scenario_name]
    setup_lockfile_method_mocks(
            testcase, testcase.scenario, "lockfile.PIDLockFile")
    testcase.pidlockfile_args = dict(
            path=testcase.scenario['pidfile_path'],
            )
    testcase.test_instance = pidlockfile.PIDLockFile(
            **testcase.pidlockfile_args)
    if clear_tracker:
        testcase.mock_tracker.clear()


class TimeoutPIDLockFile_TestCase(scaffold.TestCase):
    """ Test cases for ‘TimeoutPIDLockFile’ class. """

    def setUp(self):
        """ Set up test fixtures. """
        super(TimeoutPIDLockFile_TestCase, self).setUp()

        pidlockfile_scenarios = make_pidlockfile_scenarios()
        self.pidlockfile_scenario = pidlockfile_scenarios['simple']
        pidfile_path = self.pidlockfile_scenario['pidfile_path']

        self.scenario = {
                'pidfile_path': self.pidlockfile_scenario['pidfile_path'],
                'acquire_timeout': self.getUniqueInteger(),
                }

        self.test_kwargs = dict(
                path=self.scenario['pidfile_path'],
                acquire_timeout=self.scenario['acquire_timeout'],
                )
        self.test_instance = pidfile.TimeoutPIDLockFile(
                **self.test_kwargs)

    def tearDown(self):
        """ Tear down test fixtures. """
        super(TimeoutPIDLockFile_TestCase, self).tearDown()

    def test_inherits_from_pidlockfile(self):
        """ Should inherit from PIDLockFile. """
        instance = self.test_instance
        self.failUnlessIsInstance(instance, pidlockfile.PIDLockFile)

    def test_init_has_expected_signature(self):
        """ Should have expected signature for ‘__init__’. """
        def test_func(self, path, acquire_timeout=None, *args, **kwargs): pass
        test_func.__name__ = b'__init__'
        self.failUnlessFunctionSignatureMatch(
                test_func,
                pidfile.TimeoutPIDLockFile.__init__)

    def test_has_specified_acquire_timeout(self):
        """ Should have specified ‘acquire_timeout’ value. """
        instance = self.test_instance
        expected_timeout = self.test_kwargs['acquire_timeout']
        self.failUnlessEqual(expected_timeout, instance.acquire_timeout)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "__init__",
            autospec=True)
    def test_calls_superclass_init(self, mock_init):
        """ Should call the superclass ‘__init__’. """
        expected_path = self.test_kwargs['path']
        instance = pidfile.TimeoutPIDLockFile(
                **self.test_kwargs)
        mock_init.assert_called_with(instance, expected_path)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "acquire",
            autospec=True)
    def test_acquire_uses_specified_timeout(self, mock_acquire):
        """ Should call the superclass ‘acquire’ with specified timeout. """
        instance = self.test_instance
        test_timeout = self.getUniqueInteger()
        expected_timeout = test_timeout
        instance.acquire(test_timeout)
        mock_acquire.assert_called_with(instance, expected_timeout)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "acquire",
            autospec=True)
    def test_acquire_uses_stored_timeout_by_default(self, mock_acquire):
        """ Should call superclass ‘acquire’ with stored timeout by default. """
        instance = self.test_instance
        test_timeout = self.test_kwargs['acquire_timeout']
        expected_timeout = test_timeout
        instance.acquire()
        mock_acquire.assert_called_with(instance, expected_timeout)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
