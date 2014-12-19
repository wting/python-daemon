# -*- coding: utf-8 -*-
#
# test/test_pidlockfile.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Unit test for ‘pidlockfile’ module.
    """

from __future__ import unicode_literals

import __builtin__ as builtins
import os
from StringIO import StringIO
import itertools
import tempfile
import errno

import mock
import lockfile

import scaffold

from daemon import pidlockfile


class FakeFileDescriptorStringIO(StringIO, object):
    """ A StringIO class that fakes a file descriptor. """

    _fileno_generator = itertools.count()

    def __init__(self, *args, **kwargs):
        self._fileno = self._fileno_generator.next()
        super_instance = super(FakeFileDescriptorStringIO, self)
        super_instance.__init__(*args, **kwargs)

    def fileno(self):
        return self._fileno

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Exception_TestCase(scaffold.Exception_TestCase):
    """ Test cases for module exception classes. """

    scenarios = scaffold.make_exception_scenarios([
            ('pidlockfile.PIDFileError', dict(
                exc_type = pidlockfile.PIDFileError,
                min_args = 1,
                types = [Exception],
                )),
            ('pidlockfile.PIDFileParseError', dict(
                exc_type = pidlockfile.PIDFileParseError,
                min_args = 2,
                types = [pidlockfile.PIDFileError, ValueError],
                )),
            ])


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
                'open_func_name': 'fake_open_nonexist',
                'os_open_func_name': 'fake_os_open_nonexist',
                },
            'not-exist-write-denied': {
                'open_func_name': 'fake_open_nonexist',
                'os_open_func_name': 'fake_os_open_nonexist',
                },
            'not-exist-write-busy': {
                'open_func_name': 'fake_open_nonexist',
                'os_open_func_name': 'fake_os_open_nonexist',
                },
            'exist-read-denied': {
                'open_func_name': 'fake_open_read_denied',
                'os_open_func_name': 'fake_os_open_read_denied',
                },
            'exist-locked-read-denied': {
                'locking_pid': fake_other_pid,
                'open_func_name': 'fake_open_read_denied',
                'os_open_func_name': 'fake_os_open_read_denied',
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

    for scenario in scenarios.itervalues():
        scenario['pid'] = fake_current_pid
        scenario['pidfile_path'] = fake_pidfile_path
        if 'pidfile' not in scenario:
            scenario['pidfile'] = fake_pidfile_empty
        if 'pidfile_pid' not in scenario:
            scenario['pidfile_pid'] = None
        if 'locking_pid' not in scenario:
            scenario['locking_pid'] = None
        if 'open_func_name' not in scenario:
            scenario['open_func_name'] = 'fake_open_okay'
        if 'os_open_func_name' not in scenario:
            scenario['os_open_func_name'] = 'fake_os_open_okay'

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
                (name, obj) for (name, obj) in vars().iteritems()
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


def apply_lockfile_method_mocks(mock_lockfile, testcase, scenario):
    """ Apply common fake methods to mock lockfile class. """
    fake_methods = dict(
            (func_name, fake_func)
            for (func_name, fake_func) in
                make_lockfile_method_fakes(scenario).iteritems()
            if func_name not in ['read_pid'])

    for (func_name, fake_func) in fake_methods.iteritems():
        func_patcher = mock.patch.object(
                mock_lockfile, func_name,
                new=fake_func)
        func_patcher.start()
        testcase.addCleanup(func_patcher.stop)


def setup_pidlockfile_fixtures(testcase, scenario_name=None):
    """ Set up common fixtures for PIDLockFile test cases. """

    setup_pidfile_fixtures(testcase)

    for func_name in [
            'write_pid_to_pidfile',
            'remove_existing_pidfile',
            ]:
        func_patcher = mock.patch.object(pidlockfile, func_name)
        func_patcher.start()
        testcase.addCleanup(func_patcher.stop)

    if scenario_name is not None:
        set_pidlockfile_scenario(testcase, scenario_name)


def set_pidlockfile_scenario(testcase, scenario_name):
    """ Set up the test case to the specified scenario. """
    testcase.scenario = testcase.pidlockfile_scenarios[scenario_name]
    apply_lockfile_method_mocks(
            lockfile.LinkFileLock, testcase, testcase.scenario)
    testcase.pidlockfile_args = dict(
            path=testcase.scenario['pidfile_path'],
            )
    testcase.test_instance = pidlockfile.PIDLockFile(
            **testcase.pidlockfile_args)


class PIDLockFile_BaseTestCase(scaffold.TestCase):
    """ Base class for ‘PIDLockFile’ test case classes. """

    def setUp(self):
        """ Set up test fixtures. """
        super(PIDLockFile_BaseTestCase, self).setUp()

        setup_pidlockfile_fixtures(self)
        set_pidlockfile_scenario(self, 'simple')


class PIDLockFile_TestCase(PIDLockFile_BaseTestCase):
    """ Test cases for PIDLockFile class. """

    def test_instantiate(self):
        """ New instance of PIDLockFile should be created. """
        instance = self.test_instance
        self.assertIsInstance(instance, pidlockfile.PIDLockFile)

    def test_inherits_from_linkfilelock(self):
        """ Should inherit from LinkFileLock. """
        instance = self.test_instance
        self.assertIsInstance(instance, lockfile.LinkFileLock)

    def test_has_specified_path(self):
        """ Should have specified path. """
        instance = self.test_instance
        expect_path = self.scenario['pidfile_path']
        self.assertEqual(expect_path, instance.path)


class PIDLockFile_read_pid_TestCase(PIDLockFile_BaseTestCase):
    """ Test cases for PIDLockFile.read_pid method. """
 
    def setUp(self):
        """ Set up test fixtures. """
        super(PIDLockFile_read_pid_TestCase, self).setUp()

        setup_pidlockfile_fixtures(self, 'exist-other-pid')

    def test_gets_pid_via_read_pid_from_pidfile(self):
        """ Should get PID via read_pid_from_pidfile. """
        instance = self.test_instance
        test_pid = self.scenario['pidfile_pid']
        expect_pid = test_pid
        result = instance.read_pid()
        self.assertEqual(expect_pid, result)


class PIDLockFile_acquire_TestCase(PIDLockFile_BaseTestCase):
    """ Test cases for PIDLockFile.acquire function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(PIDLockFile_acquire_TestCase, self).setUp()

        setup_pidlockfile_fixtures(self)
        set_pidlockfile_scenario(self, 'not-exist')

    def test_calls_linkfilelock_acquire(self):
        """ Should first call LinkFileLock.acquire method. """
        instance = self.test_instance
        instance.acquire()
        lockfile.LinkFileLock.acquire.assert_called_with()

    def test_calls_linkfilelock_acquire_with_timeout(self):
        """ Should call LinkFileLock.acquire method with specified timeout. """
        instance = self.test_instance
        test_timeout = object()
        instance.acquire(timeout=test_timeout)
        lockfile.LinkFileLock.acquire.assert_called_with(timeout=test_timeout)

    def test_writes_pid_to_specified_file(self):
        """ Should request writing current PID to specified file. """
        instance = self.test_instance
        pidfile_path = self.scenario['pidfile_path']
        instance.acquire()
        pidlockfile.write_pid_to_pidfile.assert_called_with(pidfile_path)

    def test_raises_lock_failed_on_write_error(self):
        """ Should raise LockFailed error if write fails. """
        set_pidlockfile_scenario(self, 'not-exist-write-busy')
        instance = self.test_instance
        pidfile_path = self.scenario['pidfile_path']
        test_error = OSError(errno.EBUSY, "Bad stuff", pidfile_path)
        pidlockfile.write_pid_to_pidfile.side_effect = test_error
        expected_error = pidlockfile.LockFailed
        self.assertRaises(
                expected_error,
                instance.acquire)


class PIDLockFile_release_TestCase(PIDLockFile_BaseTestCase):
    """ Test cases for PIDLockFile.release function. """

    def test_does_not_remove_existing_pidfile_if_not_locking(self):
        """ Should not request removal of PID file if not locking. """
        set_pidlockfile_scenario(self, 'exist-empty')
        instance = self.test_instance
        expected_error = lockfile.NotLocked
        self.assertRaises(
                expected_error,
                instance.release)
        self.assertFalse(pidlockfile.remove_existing_pidfile.called)

    def test_does_not_remove_existing_pidfile_if_not_my_lock(self):
        """ Should not request removal of PID file if we are not locking. """
        set_pidlockfile_scenario(self, 'exist-other-pid-locked')
        instance = self.test_instance
        expected_error = lockfile.NotMyLock
        self.assertRaises(
                expected_error,
                instance.release)
        self.assertFalse(pidlockfile.remove_existing_pidfile.called)

    def test_removes_existing_pidfile_if_i_am_locking(self):
        """ Should request removal of specified PID file if lock is ours. """
        set_pidlockfile_scenario(self, 'exist-current-pid-locked')
        instance = self.test_instance
        pidfile_path = self.scenario['pidfile_path']
        instance.release()
        pidlockfile.remove_existing_pidfile.assert_called_with(pidfile_path)

    def test_calls_linkfilelock_release(self):
        """ Should finally call LinkFileLock.release method. """
        set_pidlockfile_scenario(self, 'exist-current-pid-locked')
        instance = self.test_instance
        instance.release()
        lockfile.LinkFileLock.release.assert_called_with()


class PIDLockFile_break_lock_TestCase(PIDLockFile_BaseTestCase):
    """ Test cases for PIDLockFile.break_lock function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(PIDLockFile_break_lock_TestCase, self).setUp()

        setup_pidlockfile_fixtures(self)
        set_pidlockfile_scenario(self, 'exist-other-pid-locked')

    def test_calls_linkfilelock_break_lock(self):
        """ Should first call LinkFileLock.break_lock method. """
        instance = self.test_instance
        instance.break_lock()
        lockfile.LinkFileLock.break_lock.assert_called_with()

    def test_removes_existing_pidfile(self):
        """ Should request removal of specified PID file. """
        instance = self.test_instance
        pidfile_path = self.scenario['pidfile_path']
        instance.break_lock()
        pidlockfile.remove_existing_pidfile.assert_called_with(pidfile_path)


class read_pid_from_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for read_pid_from_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(read_pid_from_pidfile_TestCase, self).setUp()

        setup_pidfile_fixtures(self)

    def test_opens_specified_filename(self):
        """ Should attempt to open specified pidfile filename. """
        set_pidlockfile_scenario(self, 'exist-other-pid')
        pidfile_path = self.scenario['pidfile_path']
        dummy = pidlockfile.read_pid_from_pidfile(pidfile_path)
        builtins.open.assert_called_with(pidfile_path, 'r')

    def test_reads_pid_from_file(self):
        """ Should read the PID from the specified file. """
        set_pidlockfile_scenario(self, 'exist-other-pid')
        pidfile_path = self.scenario['pidfile_path']
        expected_pid = self.scenario['pidfile_pid']
        pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
        self.assertEqual(expected_pid, pid)

    def test_returns_none_when_file_nonexist(self):
        """ Should return None when the PID file does not exist. """
        set_pidlockfile_scenario(self, 'not-exist')
        pidfile_path = self.scenario['pidfile_path']
        pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
        self.assertIs(None, pid)

    def test_raises_error_when_file_read_fails(self):
        """ Should raise error when the PID file read fails. """
        set_pidlockfile_scenario(self, 'exist-read-denied')
        pidfile_path = self.scenario['pidfile_path']
        expected_error = EnvironmentError
        self.assertRaises(
                expected_error,
                pidlockfile.read_pid_from_pidfile, pidfile_path)

    def test_raises_error_when_file_empty(self):
        """ Should raise error when the PID file is empty. """
        set_pidlockfile_scenario(self, 'exist-empty')
        pidfile_path = self.scenario['pidfile_path']
        expected_error = pidlockfile.PIDFileParseError
        self.assertRaises(
                expected_error,
                pidlockfile.read_pid_from_pidfile, pidfile_path)

    def test_raises_error_when_file_contents_invalid(self):
        """ Should raise error when the PID file contents are invalid. """
        set_pidlockfile_scenario(self, 'exist-invalid')
        pidfile_path = self.scenario['pidfile_path']
        expected_error = pidlockfile.PIDFileParseError
        self.assertRaises(
                expected_error,
                pidlockfile.read_pid_from_pidfile, pidfile_path)


@mock.patch.object(os, "remove")
class remove_existing_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for remove_existing_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(remove_existing_pidfile_TestCase, self).setUp()

        setup_pidfile_fixtures(self)

    def test_removes_specified_filename(
            self, mock_func_os_remove):
        """ Should attempt to remove specified PID file filename. """
        set_pidlockfile_scenario(self, 'exist-current-pid')
        pidfile_path = self.scenario['pidfile_path']
        pidlockfile.remove_existing_pidfile(pidfile_path)
        mock_func_os_remove.assert_called_with(pidfile_path)

    def test_ignores_file_not_exist_error(
            self, mock_func_os_remove):
        """ Should ignore error if file does not exist. """
        set_pidlockfile_scenario(self, 'not-exist')
        pidfile_path = self.scenario['pidfile_path']
        test_error = OSError(errno.ENOENT, "Not there", pidfile_path)
        mock_func_os_remove.side_effect = test_error
        pidlockfile.remove_existing_pidfile(pidfile_path)
        mock_func_os_remove.assert_called_with(pidfile_path)

    def test_propagates_arbitrary_oserror(
            self, mock_func_os_remove):
        """ Should propagate any OSError other than ENOENT. """
        set_pidlockfile_scenario(self, 'exist-current-pid')
        pidfile_path = self.scenario['pidfile_path']
        test_error = OSError(errno.EACCES, "Denied", pidfile_path)
        mock_func_os_remove.side_effect = test_error
        self.assertRaises(
                type(test_error),
                pidlockfile.remove_existing_pidfile,
                pidfile_path)


class write_pid_to_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for write_pid_to_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(write_pid_to_pidfile_TestCase, self).setUp()

        setup_pidfile_fixtures(self)
        set_pidlockfile_scenario(self, 'not-exist')

    def test_opens_specified_filename(self):
        """ Should attempt to open specified PID file filename. """
        pidfile_path = self.scenario['pidfile_path']
        expected_flags = (os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        expected_mode = 0644
        pidlockfile.write_pid_to_pidfile(pidfile_path)
        os.open.assert_called_with(pidfile_path, expected_flags, expected_mode)

    def test_writes_pid_to_file(self):
        """ Should write the current PID to the specified file. """
        pidfile_path = self.scenario['pidfile_path']
        expected_content = "%(pid)d\n" % self.scenario
        with mock.patch.object(
                self.scenario['pidfile'], "close") as mock_func_close:
            pidlockfile.write_pid_to_pidfile(pidfile_path)
        self.assertEqual(expected_content, self.scenario['pidfile'].getvalue())

    def test_closes_file_after_write(self):
        """ Should close the specified file after writing. """
        pidfile_path = self.scenario['pidfile_path']
        expected_calls = [
                mock.call.write(mock.ANY),
                mock.call.close(),
                ]
        mock_pidfile = mock.Mock()
        with mock.patch.object(
                self.scenario['pidfile'], "write") as mock_func_write:
            with mock.patch.object(
                    self.scenario['pidfile'], "close") as mock_func_close:
                mock_pidfile.attach_mock(mock_func_write, "write")
                mock_pidfile.attach_mock(mock_func_close, "close")
                pidlockfile.write_pid_to_pidfile(pidfile_path)
        mock_pidfile.assert_has_calls(expected_calls)


class TimeoutPIDLockFile_TestCase(scaffold.TestCase):
    """ Test cases for ‘TimeoutPIDLockFile’ class. """

    def setUp(self):
        """ Set up test fixtures. """
        super(TimeoutPIDLockFile_TestCase, self).setUp()

        pidlockfile_scenarios = make_pidlockfile_scenarios()
        self.pidlockfile_scenario = pidlockfile_scenarios['simple']
        pidfile_path = self.pidlockfile_scenario['pidfile_path']

        for func_name in ['__init__', 'acquire']:
            func_patcher = mock.patch.object(
                    pidlockfile.PIDLockFile, func_name)
            func_patcher.start()
            self.addCleanup(func_patcher.stop)

        self.scenario = {
                'pidfile_path': self.pidlockfile_scenario['pidfile_path'],
                'acquire_timeout': self.getUniqueInteger(),
                }

        self.test_kwargs = dict(
                path=self.scenario['pidfile_path'],
                acquire_timeout=self.scenario['acquire_timeout'],
                )
        self.test_instance = pidlockfile.TimeoutPIDLockFile(
                **self.test_kwargs)

    def test_inherits_from_pidlockfile(self):
        """ Should inherit from PIDLockFile. """
        instance = self.test_instance
        self.assertIsInstance(instance, pidlockfile.PIDLockFile)

    def test_init_has_expected_signature(self):
        """ Should have expected signature for ‘__init__’. """
        def test_func(self, path, acquire_timeout=None, *args, **kwargs): pass
        test_func.__name__ = b'__init__'
        self.assertFunctionSignatureMatch(
                test_func,
                pidlockfile.TimeoutPIDLockFile.__init__)

    def test_has_specified_acquire_timeout(self):
        """ Should have specified ‘acquire_timeout’ value. """
        instance = self.test_instance
        expected_timeout = self.test_kwargs['acquire_timeout']
        self.assertEqual(expected_timeout, instance.acquire_timeout)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "__init__",
            autospec=True)
    def test_calls_superclass_init(self, mock_init):
        """ Should call the superclass ‘__init__’. """
        expected_path = self.test_kwargs['path']
        instance = pidlockfile.TimeoutPIDLockFile(**self.test_kwargs)
        mock_init.assert_called_with(instance, expected_path)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "acquire",
            autospec=True)
    def test_acquire_uses_specified_timeout(self, mock_func_acquire):
        """ Should call the superclass ‘acquire’ with specified timeout. """
        instance = self.test_instance
        test_timeout = self.getUniqueInteger()
        expected_timeout = test_timeout
        instance.acquire(test_timeout)
        mock_func_acquire.assert_called_with(instance, expected_timeout)

    @mock.patch.object(
            pidlockfile.PIDLockFile, "acquire",
            autospec=True)
    def test_acquire_uses_stored_timeout_by_default(self, mock_func_acquire):
        """ Should call superclass ‘acquire’ with stored timeout by default. """
        instance = self.test_instance
        test_timeout = self.test_kwargs['acquire_timeout']
        expected_timeout = test_timeout
        instance.acquire()
        mock_func_acquire.assert_called_with(instance, expected_timeout)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
