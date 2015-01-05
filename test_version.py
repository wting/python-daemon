# -*- coding: utf-8 -*-
#
# test_version.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3 of that license or any later version.
# No warranty expressed or implied. See the file ‘LICENSE.GPL-3’ for details.

""" Unit test for ‘version’ packaging module. """

from __future__ import (absolute_import, unicode_literals)

import collections

import mock
import testtools
import testscenarios
import docutils

import version
from version import (basestring, unicode)


class VersionInfoWriter_TestCase(testtools.TestCase):
    """ Test cases for ‘VersionInfoWriter’ class. """

    def setUp(self):
        """ Set up test fixtures. """
        super(VersionInfoWriter_TestCase, self).setUp()

        self.test_instance = version.VersionInfoWriter()

    def test_declares_version_info_support(self):
        """ Should declare support for ‘version_info’. """
        instance = self.test_instance
        expected_support = "version_info"
        result = instance.supports(expected_support)
        self.assertTrue(result)


class VersionInfoWriter_translate_TestCase(testtools.TestCase):
    """ Test cases for ‘VersionInfoWriter.translate’ method. """

    def setUp(self):
        """ Set up test fixtures. """
        super(VersionInfoWriter_translate_TestCase, self).setUp()

        patcher_translator = mock.patch.object(
                version, 'VersionInfoTranslator')
        self.mock_class_translator = patcher_translator.start()
        self.addCleanup(patcher_translator.stop)
        self.mock_translator = self.mock_class_translator.return_value

        self.test_instance = version.VersionInfoWriter()
        patcher_document = mock.patch.object(
                self.test_instance, 'document')
        patcher_document.start()
        self.addCleanup(patcher_document.stop)

    def test_creates_translator_with_document(self):
        """ Should create a translator with the writer's document. """
        instance = self.test_instance
        expected_document = self.test_instance.document
        instance.translate()
        self.mock_class_translator.assert_called_with(expected_document)

    def test_calls_document_walkabout_with_translator(self):
        """ Should call document.walkabout with the translator. """
        instance = self.test_instance
        instance.translate()
        instance.document.walkabout.assert_called_with(self.mock_translator)

    def test_output_from_translator_astext(self):
        """ Should have output from translator.astext(). """
        instance = self.test_instance
        instance.translate()
        expected_output = self.mock_translator.astext.return_value
        self.assertEqual(expected_output, instance.output)


class NewsEntry_TestCase(testtools.TestCase):
    """ Test cases for ‘NewsEntry’ class. """

    def setUp(self):
        """ Set up test fixtures. """
        super(NewsEntry_TestCase, self).setUp()

        self.test_instance = version.NewsEntry()

    def test_instantiate(self):
        """ New instance of ‘NewsEntry’ should be created. """
        self.assertIsInstance(
                self.test_instance, version.NewsEntry)

    def test_minimum_zero_arguments(self):
        """ Initialiser should not require any arguments. """
        instance = version.NewsEntry()
        self.assertIsNot(instance, None)


class NewsEntry_release_date_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘NewsEntry.release_date’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_release_date':
                    version.NewsEntry.default_release_date,
                }),
            ('unknown token', {
                'test_args': {'release_date': "UNKNOWN"},
                'expected_release_date': "UNKNOWN",
                }),
            ('future token', {
                'test_args': {'release_date': "FUTURE"},
                'expected_release_date': "FUTURE",
                }),
            ('2001-01-01', {
                'test_args': {'release_date': "2001-01-01"},
                'expected_release_date': "2001-01-01",
                }),
            ('bogus', {
                'test_args': {'release_date': "b0gUs"},
                'expected_error': ValueError,
                }),
            ]

    def test_has_expected_release_date(self):
        """ Should have default `release_date` attribute. """
        if hasattr(self, 'expected_error'):
            self.assertRaises(
                    self.expected_error,
                    version.NewsEntry, **self.test_args)
        else:
            instance = version.NewsEntry(**self.test_args)
            self.assertEqual(self.expected_release_date, instance.release_date)


class NewsEntry_version_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘NewsEntry.version’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_version':
                    version.NewsEntry.default_version,
                }),
            ('unknown token', {
                'test_args': {'version': "UNKNOWN"},
                'expected_version': "UNKNOWN",
                }),
            ('0.0', {
                'test_args': {'version': "0.0"},
                'expected_version': "0.0",
                }),
            ]

    def test_has_expected_version(self):
        """ Should have default `version` attribute. """
        instance = version.NewsEntry(**self.test_args)
        self.assertEqual(self.expected_version, instance.version)


class NewsEntry_maintainer_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘NewsEntry.maintainer’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_maintainer': None,
                }),
            ('person', {
                'test_args': {'maintainer': "Foo Bar <foo.bar@example.org>"},
                'expected_maintainer': "Foo Bar <foo.bar@example.org>",
                }),
            ('bogus', {
                'test_args': {'maintainer': "b0gUs"},
                'expected_error': ValueError,
                }),
            ]

    def test_has_expected_maintainer(self):
        """ Should have default `maintainer` attribute. """
        if hasattr(self, 'expected_error'):
            self.assertRaises(
                    self.expected_error,
                    version.NewsEntry, **self.test_args)
        else:
            instance = version.NewsEntry(**self.test_args)
            self.assertEqual(self.expected_maintainer, instance.maintainer)


class NewsEntry_body_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘NewsEntry.body’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_body': None,
                }),
            ('simple', {
                'test_args': {'body': "Foo bar baz."},
                'expected_body': "Foo bar baz.",
                }),
            ]

    def test_has_expected_body(self):
        """ Should have default `body` attribute. """
        instance = version.NewsEntry(**self.test_args)
        self.assertEqual(self.expected_body, instance.body)


class NewsEntry_as_version_info_entry_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘NewsEntry.as_version_info_entry’ attribute. """

    scenarios = [
        ('default', {
            'test_args': {},
            'expected_result': collections.OrderedDict([
                ('release_date', version.NewsEntry.default_release_date),
                ('version', version.NewsEntry.default_version),
                ('maintainer', None),
                ('body', None),
                ]),
            }),
        ]

    def setUp(self):
        """ Set up test fixtures. """
        super(NewsEntry_as_version_info_entry_TestCase, self).setUp()

        self.test_instance = version.NewsEntry(**self.test_args)

    def test_returns_result(self):
        """ Should return expected result. """
        result = self.test_instance.as_version_info_entry()
        self.assertEqual(self.expected_result, result)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
