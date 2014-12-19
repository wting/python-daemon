# -*- coding: utf-8 -*-

# test/scaffold.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2007–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Scaffolding for unit test modules.
    """

from __future__ import unicode_literals

import unittest
from unittest import (
        TestSuite,
        TestLoader,
        )
import doctest
import logging
import os
import sys
import operator
import textwrap
from copy import deepcopy
import itertools
try:
    # Python 2.6 or greater?
    from functools import reduce
except ImportError:
    # Not available, so try the builtin function.
    assert reduce

import testscenarios
import testtools.testcase


test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
if not test_dir in sys.path:
    sys.path.insert(1, test_dir)
if not parent_dir in sys.path:
    sys.path.insert(1, parent_dir)

# Disable all but the most critical logging messages.
logging.disable(logging.CRITICAL)


def get_python_module_names(file_list, file_suffix='.py'):
    """ Return a list of module names from a filename list. """
    module_names = [
            m[:m.rfind(file_suffix)] for m in file_list
            if m.endswith(file_suffix)]
    return module_names


def get_test_module_names(module_list, module_prefix='test_'):
    """ Return the list of module names that qualify as test modules. """
    module_names = [
            m for m in module_list
            if m.startswith(module_prefix)]
    return module_names


def make_suite(path=test_dir):
    """ Create the test suite for the given path. """
    loader = unittest.TestLoader()
    python_module_names = get_python_module_names(os.listdir(path))
    test_module_names = get_test_module_names(python_module_names)
    suite = loader.loadTestsFromNames(test_module_names)

    return suite


def get_function_signature(func):
    """ Get the function signature as a mapping of attributes. """
    arg_count = func.func_code.co_argcount
    arg_names = func.func_code.co_varnames[:arg_count]

    arg_defaults = {}
    func_defaults = ()
    if func.func_defaults is not None:
        func_defaults = func.func_defaults
    for (name, value) in itertools.izip(arg_names[::-1], func_defaults[::-1]):
        arg_defaults[name] = value

    signature = {
            'name': func.__name__,
            'arg_count': arg_count,
            'arg_names': arg_names,
            'arg_defaults': arg_defaults,
            }

    non_pos_names = list(func.func_code.co_varnames[arg_count:])
    COLLECTS_ARBITRARY_POSITIONAL_ARGS = 0x04
    if func.func_code.co_flags & COLLECTS_ARBITRARY_POSITIONAL_ARGS:
        signature['var_args'] = non_pos_names.pop(0)
    COLLECTS_ARBITRARY_KEYWORD_ARGS = 0x08
    if func.func_code.co_flags & COLLECTS_ARBITRARY_KEYWORD_ARGS:
        signature['var_kw_args'] = non_pos_names.pop(0)

    return signature


def format_function_signature(func):
    """ Format the function signature as printable text. """
    signature = get_function_signature(func)

    args_text = []
    for arg_name in signature['arg_names']:
        if arg_name in signature['arg_defaults']:
            arg_default = signature['arg_defaults'][arg_name]
            arg_text_template = "%(arg_name)s=%(arg_default)r"
        else:
            arg_text_template = "%(arg_name)s"
        args_text.append(arg_text_template % vars())
    if 'var_args' in signature:
        args_text.append("*%(var_args)s" % signature)
    if 'var_kw_args' in signature:
        args_text.append("**%(var_kw_args)s" % signature)
    signature_args_text = ", ".join(args_text)

    func_name = signature['name']
    signature_text = (
            "%(func_name)s(%(signature_args_text)s)" % vars())

    return signature_text


class TestCase(testtools.testcase.TestCase):
    """ Test case behaviour. """

    def failUnlessOutputCheckerMatch(self, want, got, msg=None):
        """ Fail unless the specified string matches the expected.

            Fail the test unless ``want`` matches ``got``, as
            determined by a ``doctest.OutputChecker`` instance. This
            is not an equality check, but a pattern match according to
            the ``OutputChecker`` rules.

            """
        checker = doctest.OutputChecker()
        want = textwrap.dedent(want)
        source = ""
        example = doctest.Example(source, want)
        got = textwrap.dedent(got)
        checker_optionflags = reduce(operator.or_, [
                doctest.ELLIPSIS,
                ])
        if not checker.check_output(want, got, checker_optionflags):
            if msg is None:
                diff = checker.output_difference(
                        example, got, checker_optionflags)
                msg = "\n".join([
                        "Output received did not match expected output",
                        "%(diff)s",
                        ]) % vars()
            raise self.failureException(msg)

    assertOutputCheckerMatch = failUnlessOutputCheckerMatch

    def failUnlessFunctionInTraceback(self, traceback, function, msg=None):
        """ Fail if the function is not in the traceback.

            Fail the test if the function ``function`` is not at any
            of the levels in the traceback object ``traceback``.

            """
        func_in_traceback = False
        expected_code = function.func_code
        current_traceback = traceback
        while current_traceback is not None:
            if expected_code is current_traceback.tb_frame.f_code:
                func_in_traceback = True
                break
            current_traceback = current_traceback.tb_next

        if not func_in_traceback:
            if msg is None:
                msg = (
                        "Traceback did not lead to original function"
                        " %(function)s"
                        ) % vars()
            raise self.failureException(msg)

    assertFunctionInTraceback = failUnlessFunctionInTraceback

    def failUnlessFunctionSignatureMatch(self, first, second, msg=None):
        """ Fail if the function signatures do not match.

            Fail the test if the function signature does not match
            between the ``first`` function and the ``second``
            function.

            The function signature includes:

            * function name,

            * count of named parameters,

            * sequence of named parameters,

            * default values of named parameters,

            * collector for arbitrary positional arguments,

            * collector for arbitrary keyword arguments.

            """
        first_signature = get_function_signature(first)
        second_signature = get_function_signature(second)

        if first_signature != second_signature:
            if msg is None:
                first_signature_text = format_function_signature(first)
                second_signature_text = format_function_signature(second)
                msg = (textwrap.dedent("""\
                        Function signatures do not match:
                            %(first_signature)r != %(second_signature)r
                        Expected:
                            %(first_signature_text)s
                        Got:
                            %(second_signature_text)s""")
                        ) % vars()
            raise self.failureException(msg)

    assertFunctionSignatureMatch = failUnlessFunctionSignatureMatch


class TestCaseWithScenarios(testscenarios.WithScenarios, TestCase):
    """ Test cases run per scenario. """


class Exception_TestCase(TestCaseWithScenarios):
    """ Test cases for exception classes. """

    def test_exception_instance(self):
        """ Exception instance should be created. """
        self.assertIsNot(self.instance, None)

    def test_exception_types(self):
        """ Exception instance should match expected types. """
        for match_type in self.types:
            self.assertIsInstance(self.instance, match_type)


def make_exception_scenarios(scenarios):
    """ Make test scenarios for exception classes.

        Use this with `testscenarios` to adapt `Exception_TestCase`_
        for any exceptions that need testing.

        :param scenarios:
            List of scenarios Each scenario is a tuple (`name`, `map`)
            where `map` is a mapping of attributes to be applied to
            each test case. Attributes map must contain items for:

            :key exc_type:
                The exception type to be tested.
            :key min_args:
                The minimum argument count for the exception instance
                initialiser.
            :key types:
                Sequence of types that should be superclasses of each
                instance of the exception type.

        :return:
            List of scenarios with additional mapping entries.

        """
    updated_scenarios = deepcopy(scenarios)
    for (name, scenario) in updated_scenarios:
        args = (None,) * scenario['min_args']
        scenario['args'] = args
        instance = scenario['exc_type'](*args)
        scenario['instance'] = instance

    return updated_scenarios


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
