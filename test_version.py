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

import mock
import testtools
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


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
