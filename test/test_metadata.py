# -*- coding: utf-8 -*-
#
# test/test_metadata.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Unit test for ‘_metadata’ private module.
    """

from __future__ import unicode_literals

import sys
import re
import urlparse
import functools

import mock
import pkg_resources

import scaffold
import testtools.helpers
import testtools.matchers

import daemon._metadata as metadata


class HasAttribute(testtools.matchers.Matcher):
    """ A matcher to assert an object has a named attribute. """

    def __init__(self, name):
        self.attribute_name = name

    def match(self, instance):
        """ Assert the object `instance` has an attribute named `name`. """
        result = None
        if not testtools.helpers.safe_hasattr(instance, self.attribute_name):
            result = AttributeNotFoundMismatch(instance, self.attribute_name)
        return result


class AttributeNotFoundMismatch(testtools.matchers.Mismatch):
    """ The specified instance does not have the named attribute. """

    def __init__(self, instance, name):
        self.instance = instance
        self.attribute_name = name

    def describe(self):
        """ Emit a text description of this mismatch. """
        text = (
                "%(instance)r"
                " has no attribute named %(attribute_name)r") % vars(self)
        return text


class metadata_value_TestCase(scaffold.TestCaseWithScenarios):
    """ Test cases for metadata module values. """

    expected_str_attributes = set([
            'version_installed',
            'author',
            'copyright',
            'license',
            'url',
            ])

    scenarios = [
            (name, {'attribute_name': name}) for name in expected_str_attributes]
    for (name, params) in scenarios:
        # Expect an attribute of ‘str’ to test this value.
        params['ducktype_attribute_name'] = 'isdigit'

    def test_module_has_attribute(self):
        """ Metadata should have expected value as a module attribute. """
        self.assertThat(
                metadata, HasAttribute(self.attribute_name))

    def test_module_attribute_has_duck_type(self):
        """ Metadata value should have expected duck-typing attribute. """
        instance = getattr(metadata, self.attribute_name)
        self.assertThat(
                instance, HasAttribute(self.ducktype_attribute_name))


class metadata_content_TestCase(scaffold.TestCase):
    """ Test cases for content of metadata. """

    def test_copyright_formatted_correctly(self):
        """ Copyright statement should be formatted correctly. """
        regex_pattern = (
                "Copyright © "
                "\d{4}" # four-digit year
                "(?:–\d{4})" # optional range dash and ending four-digit year
                )
        regex_flags = re.UNICODE
        self.assertThat(
                metadata.copyright,
                testtools.matchers.MatchesRegex(regex_pattern, regex_flags))

    def test_author_formatted_correctly(self):
        """ Author information should be formatted correctly. """
        regex_pattern = (
                ".+ " # name
                "<[^>]+>" # email address, in angle brackets
                )
        regex_flags = re.UNICODE
        self.assertThat(
                metadata.author,
                testtools.matchers.MatchesRegex(regex_pattern, regex_flags))

    def test_copyright_contains_author(self):
        """ Copyright information should contain author information. """
        self.assertThat(
                metadata.copyright,
                testtools.matchers.Contains(metadata.author))

    def test_url_parses_correctly(self):
        """ Homepage URL should parse correctly. """
        result = urlparse.urlparse(metadata.url)
        self.assertIsInstance(
                result, urlparse.ParseResult,
                "URL value %(url)r did not parse correctly" % vars(metadata))


def fake_func_get_distribution(testcase, distribution_name):
    """ Fake the behaviour of ‘pkg_resources.get_distribution’. """
    if distribution_name != metadata.distribution_name:
        raise pkg_resources.DistributionNotFound
    if hasattr(testcase, 'get_distribution_error'):
        raise testcase.get_distribution_error
    mock_distribution = mock.MagicMock()
    if hasattr(testcase, 'test_version'):
        mock_distribution.version = testcase.test_version
    return mock_distribution
        
@mock.patch.object(pkg_resources, 'get_distribution')
@mock.patch.object(metadata, 'distribution_name', new="mock-dist")
class get_distribution_version_TestCase(scaffold.TestCaseWithScenarios):
    """ Test cases for ‘get_distribution_version’ function. """

    scenarios = [
            ('version 0.0', {
                'test_version': "0.0",
                'expected_version': "0.0",
                }),
            ('version 1.0', {
                'test_version': "1.0",
                'expected_version': "1.0",
                }),
            ('not installed', {
                'get_distribution_error': pkg_resources.DistributionNotFound(),
                'expected_version': None,
                }),
            ]

    def test_requests_installed_distribution(
            self, mock_func_get_distribution):
        """ The package distribution should be retrieved. """
        mock_func_get_distribution.side_effect = functools.partial(
                fake_func_get_distribution, self)
        expected_distribution_name = metadata.distribution_name
        version = metadata.get_distribution_version()
        mock_func_get_distribution.assert_called_with(
                expected_distribution_name)

    def test_version_installed_matches_distribution(
            self, mock_func_get_distribution):
        """ The ‘version_installed’ value should match the distribution. """
        mock_func_get_distribution.side_effect = functools.partial(
                fake_func_get_distribution, self)
        version = metadata.get_distribution_version()
        self.assertEqual(version, self.expected_version)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
