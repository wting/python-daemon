# -*- coding: utf-8 -*-
#
# test_version.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2015 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3 of that license or any later version.
# No warranty expressed or implied. See the file ‘LICENSE.GPL-3’ for details.

""" Unit test for ‘version’ packaging module. """

from __future__ import (absolute_import, unicode_literals)

try:
    # Python 3 standard library.
    import builtins
except ImportError:
    # Python 2 standard library.
    import __builtin__ as builtins
import os
import os.path
import errno
import functools
import collections
import textwrap
import json
import tempfile
import distutils.dist
import distutils.cmd
import distutils.errors
try:
    # Standard library of Python 2.7 and later.
    from io import StringIO
except ImportError:
    # Standard library of Python 2.6 and earlier.
    from StringIO import StringIO

import mock
import testtools
import testscenarios
import docutils

import version


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


class ChangeLogEntry_TestCase(testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry’ class. """

    def setUp(self):
        """ Set up test fixtures. """
        super(ChangeLogEntry_TestCase, self).setUp()

        self.test_instance = version.ChangeLogEntry()

    def test_instantiate(self):
        """ New instance of ‘ChangeLogEntry’ should be created. """
        self.assertIsInstance(
                self.test_instance, version.ChangeLogEntry)

    def test_minimum_zero_arguments(self):
        """ Initialiser should not require any arguments. """
        instance = version.ChangeLogEntry()
        self.assertIsNot(instance, None)


class ChangeLogEntry_release_date_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry.release_date’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_release_date':
                    version.ChangeLogEntry.default_release_date,
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
                    version.ChangeLogEntry, **self.test_args)
        else:
            instance = version.ChangeLogEntry(**self.test_args)
            self.assertEqual(self.expected_release_date, instance.release_date)


class ChangeLogEntry_version_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry.version’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_version':
                    version.ChangeLogEntry.default_version,
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
        instance = version.ChangeLogEntry(**self.test_args)
        self.assertEqual(self.expected_version, instance.version)


class ChangeLogEntry_maintainer_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry.maintainer’ attribute. """

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
                    version.ChangeLogEntry, **self.test_args)
        else:
            instance = version.ChangeLogEntry(**self.test_args)
            self.assertEqual(self.expected_maintainer, instance.maintainer)


class ChangeLogEntry_body_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry.body’ attribute. """

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
        instance = version.ChangeLogEntry(**self.test_args)
        self.assertEqual(self.expected_body, instance.body)


class ChangeLogEntry_as_version_info_entry_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘ChangeLogEntry.as_version_info_entry’ attribute. """

    scenarios = [
            ('default', {
                'test_args': {},
                'expected_result': collections.OrderedDict([
                    ('release_date', version.ChangeLogEntry.default_release_date),
                    ('version', version.ChangeLogEntry.default_version),
                    ('maintainer', None),
                    ('body', None),
                    ]),
                }),
            ]

    def setUp(self):
        """ Set up test fixtures. """
        super(ChangeLogEntry_as_version_info_entry_TestCase, self).setUp()

        self.test_instance = version.ChangeLogEntry(**self.test_args)

    def test_returns_result(self):
        """ Should return expected result. """
        result = self.test_instance.as_version_info_entry()
        self.assertEqual(self.expected_result, result)


def make_mock_field_node(field_name, field_body):
    """ Make a mock Docutils field node for tests. """

    mock_field_node = mock.MagicMock(
            name='field', spec=docutils.nodes.field)

    mock_field_name_node = mock.MagicMock(
            name='field_name', spec=docutils.nodes.field_name)
    mock_field_name_node.parent = mock_field_node
    mock_field_name_node.children = [field_name]

    mock_field_body_node = mock.MagicMock(
            name='field_body', spec=docutils.nodes.field_body)
    mock_field_body_node.parent = mock_field_node
    mock_field_body_node.children = [field_body]

    mock_field_node.children = [mock_field_name_node, mock_field_body_node]

    def fake_func_first_child_matching_class(node_class):
        result = None
        node_class_name = node_class.__name__
        for (index, node) in enumerate(mock_field_node.children):
            if node._mock_name == node_class_name:
                result = index
                break
        return result

    mock_field_node.first_child_matching_class.side_effect = (
            fake_func_first_child_matching_class)

    return mock_field_node


class get_name_for_field_body_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘get_name_for_field_body’ function. """

    scenarios = [
            ('simple', {
                'test_field_node': make_mock_field_node("Foo", "spam"),
                'expected_field_name': "Foo",
                }),
            ]

    def test_returns_expected_field_name(self):
        """ Should return expected field name. """
        field_body_node = self.test_field_node.children[1]
        result = version.get_name_for_field_body(field_body_node)
        self.assertEqual(self.expected_field_name, result)


class JsonEqual(testtools.matchers.Matcher):
    """ A matcher to compare the value of JSON streams. """

    def __init__(self, expected):
        self.expected_value = expected

    def match(self, content):
        """ Assert the JSON `content` matches the `expected_content`. """
        result = None
        actual_value = json.loads(content.decode('utf-8'))
        if actual_value != self.expected_value:
            result = JsonValueMismatch(self.expected_value, actual_value)
        return result


class JsonValueMismatch(testtools.matchers.Mismatch):
    """ The specified JSON stream does not evaluate to the expected value. """

    def __init__(self, expected, actual):
        self.expected_value = expected
        self.actual_value = actual

    def describe(self):
        """ Emit a text description of this mismatch. """
        expected_json_text = json.dumps(self.expected_value, indent=4)
        actual_json_text = json.dumps(self.actual_value, indent=4)
        text = (
                "\n"
                "reference: {expected}\n"
                "actual: {actual}\n").format(
                    expected=expected_json_text, actual=actual_json_text)
        return text


class changelog_to_version_info_collection_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘changelog_to_version_info_collection’ function. """

    scenarios = [
            ('single entry', {
                'test_input': textwrap.dedent("""\
                    Version 1.0
                    ===========

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_version_info': [
                    {
                        'release_date': "2009-01-01",
                        'version': "1.0",
                        'maintainer': "Foo Bar <foo.bar@example.org>",
                        'body': "* Lorem ipsum dolor sit amet.\n",
                        },
                    ],
                }),
            ('multiple entries', {
                'test_input': textwrap.dedent("""\
                    Version 1.0
                    ===========

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.


                    Version 0.8
                    ===========

                    :Released: 2004-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Donec venenatis nisl aliquam ipsum.


                    Version 0.7.2
                    =============

                    :Released: 2001-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Pellentesque elementum mollis finibus.
                    """),
                'expected_version_info': [
                    {
                        'release_date': "2009-01-01",
                        'version': "1.0",
                        'maintainer': "Foo Bar <foo.bar@example.org>",
                        'body': "* Lorem ipsum dolor sit amet.\n",
                        },
                    {
                        'release_date': "2004-01-01",
                        'version': "0.8",
                        'maintainer': "Foo Bar <foo.bar@example.org>",
                        'body': "* Donec venenatis nisl aliquam ipsum.\n",
                        },
                    {
                        'release_date': "2001-01-01",
                        'version': "0.7.2",
                        'maintainer': "Foo Bar <foo.bar@example.org>",
                        'body': "* Pellentesque elementum mollis finibus.\n",
                        },
                    ],
                }),
            ('trailing comment', {
                'test_input': textwrap.dedent("""\
                    Version NEXT
                    ============

                    :Released: FUTURE
                    :Maintainer:

                    * Lorem ipsum dolor sit amet.

                    ..
                        Vivamus aliquam felis rutrum rutrum dictum.
                    """),
                'expected_version_info': [
                    {
                        'release_date': "FUTURE",
                        'version': "NEXT",
                        'maintainer': "",
                        'body': "* Lorem ipsum dolor sit amet.\n",
                        },
                    ],
                }),
            ('inline comment', {
                'test_input': textwrap.dedent("""\
                    Version NEXT
                    ============

                    :Released: FUTURE
                    :Maintainer:

                    ..
                        Vivamus aliquam felis rutrum rutrum dictum.

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_version_info': [
                    {
                        'release_date': "FUTURE",
                        'version': "NEXT",
                        'maintainer': "",
                        'body': "* Lorem ipsum dolor sit amet.\n",
                        },
                    ],
                }),
            ('unreleased entry', {
                'test_input': textwrap.dedent("""\
                    Version NEXT
                    ============

                    :Released: FUTURE
                    :Maintainer:

                    * Lorem ipsum dolor sit amet.


                    Version 0.8
                    ===========

                    :Released: 2001-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Donec venenatis nisl aliquam ipsum.
                    """),
                'expected_version_info': [
                    {
                        'release_date': "FUTURE",
                        'version': "NEXT",
                        'maintainer': "",
                        'body': "* Lorem ipsum dolor sit amet.\n",
                        },
                    {
                        'release_date': "2001-01-01",
                        'version': "0.8",
                        'maintainer': "Foo Bar <foo.bar@example.org>",
                        'body': "* Donec venenatis nisl aliquam ipsum.\n",
                        },
                    ],
                }),
            ('no section', {
                'test_input': textwrap.dedent("""\
                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_error': version.InvalidFormatError,
                }),
            ('subsection', {
                'test_input': textwrap.dedent("""\
                    Version 1.0
                    ===========

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.

                    Ut ultricies fermentum quam
                    ---------------------------

                    * In commodo magna facilisis in.
                    """),
                'expected_error': version.InvalidFormatError,
                'subsection': True,
                }),
            ('unknown field', {
                'test_input': textwrap.dedent("""\
                    Version 1.0
                    ===========

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>
                    :Favourite: Spam

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_error': version.InvalidFormatError,
                }),
            ('invalid version word', {
                'test_input': textwrap.dedent("""\
                    BoGuS 1.0
                    =========

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_error': version.InvalidFormatError,
                }),
            ('invalid section title', {
                'test_input': textwrap.dedent("""\
                    Lorem Ipsum 1.0
                    ===============

                    :Released: 2009-01-01
                    :Maintainer: Foo Bar <foo.bar@example.org>

                    * Lorem ipsum dolor sit amet.
                    """),
                'expected_error': version.InvalidFormatError,
                }),
            ]

    def test_returns_expected_version_info(self):
        """ Should return expected version info mapping. """
        args = {
                'infile': StringIO(self.test_input),
                'writer': version.VersionInfoWriter(),
                }
        if hasattr(self, 'expected_error'):
            self.assertRaises(
                    self.expected_error,
                    version.changelog_to_version_info_collection, **args)
        else:
            result = version.changelog_to_version_info_collection(**args)
            self.assertThat(result, JsonEqual(self.expected_version_info))


try:
    FileNotFoundError
    PermissionError
except NameError:
    # Python 2 uses OSError.
    FileNotFoundError = functools.partial(OSError, errno.ENOENT)
    PermissionError = functools.partial(OSError, errno.EPERM)

fake_version_info = {
        'release_date': "2001-01-01", 'version': "2.0",
        'maintainer': None, 'body': None,
        }

@mock.patch.object(
        version, "get_latest_version", return_value=fake_version_info)
@mock.patch.object(
        version, "changelog_to_version_info_collection")
class generate_version_info_from_changelog_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘generate_version_info_from_changelog’ function. """

    fake_open_side_effects = {
            'success': (
                lambda *args, **kwargs: StringIO()),
            'file not found': FileNotFoundError(),
            'permission denied': PermissionError(),
            }

    scenarios = [
            ('simple', {
                'open_scenario': 'success',
                'fake_versions_json': json.dumps([fake_version_info]),
                'expected_result': fake_version_info,
                }),
            ('file not found', {
                'open_scenario': 'file not found',
                'expected_result': {},
                }),
            ('permission denied', {
                'open_scenario': 'permission denied',
                'expected_result': {},
                }),
            ]

    def setUp(self):
        """ Set up test fixtures. """
        super(generate_version_info_from_changelog_TestCase, self).setUp()

        self.fake_changelog_file_path = tempfile.mktemp()

        def fake_open(filename, mode='rt', buffering=None):
            if filename == self.fake_changelog_file_path:
                side_effect = self.fake_open_side_effects[self.open_scenario]
                if hasattr(side_effect, '__call__'):
                    result = side_effect(filename, mode, buffering)
                else:
                    raise side_effect
            else:
                result = StringIO()
            return result

        mock_open = mock.mock_open()
        mock_open.side_effect = fake_open

        func_patcher_builtin_open = mock.patch.object(
                builtins, "open",
                new=mock_open)
        func_patcher_builtin_open.start()
        self.addCleanup(func_patcher_builtin_open.stop)

    def test_returns_empty_collection_on_read_error(
            self,
            mock_func_changelog_to_version_info, mock_func_get_latest_version):
        """ Should return empty collection on error reading changelog. """
        test_error = PermissionError("Not for you")
        mock_func_changelog_to_version_info.side_effect = test_error
        result = version.generate_version_info_from_changelog(
                self.fake_changelog_file_path)
        expected_result = {}
        self.assertDictEqual(expected_result, result)

    def test_returns_expected_result(
            self,
            mock_func_changelog_to_version_info, mock_func_get_latest_version):
        """ Should return expected result. """
        if hasattr(self, 'fake_versions_json'):
            mock_func_changelog_to_version_info.return_value = (
                    self.fake_versions_json.encode('utf-8'))
        result = version.generate_version_info_from_changelog(
                self.fake_changelog_file_path)
        self.assertEqual(self.expected_result, result)


DefaultNoneDict = functools.partial(collections.defaultdict, lambda: None)

class get_latest_version_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘get_latest_version’ function. """

    scenarios = [
            ('simple', {
                'test_versions': [
                    DefaultNoneDict({'release_date': "LATEST"}),
                    ],
                'expected_result': version.ChangeLogEntry.make_ordered_dict(
                    DefaultNoneDict({'release_date': "LATEST"})),
                }),
            ('no versions', {
                'test_versions': [],
                'expected_result': collections.OrderedDict(),
                }),
            ('ordered versions', {
                'test_versions': [
                    DefaultNoneDict({'release_date': "1"}),
                    DefaultNoneDict({'release_date': "2"}),
                    DefaultNoneDict({'release_date': "LATEST"}),
                    ],
                'expected_result': version.ChangeLogEntry.make_ordered_dict(
                    DefaultNoneDict({'release_date': "LATEST"})),
                }),
            ('un-ordered versions', {
                'test_versions': [
                    DefaultNoneDict({'release_date': "2"}),
                    DefaultNoneDict({'release_date': "LATEST"}),
                    DefaultNoneDict({'release_date': "1"}),
                    ],
                'expected_result': version.ChangeLogEntry.make_ordered_dict(
                    DefaultNoneDict({'release_date': "LATEST"})),
                }),
            ]

    def test_returns_expected_result(self):
        """ Should return expected result. """
        result = version.get_latest_version(self.test_versions)
        self.assertDictEqual(self.expected_result, result)


@mock.patch.object(json, "dumps", side_effect=json.dumps)
class serialise_version_info_from_mapping_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘get_latest_version’ function. """

    scenarios = [
            ('simple', {
                'test_version_info': {'foo': "spam"},
                }),
            ]

    for (name, scenario) in scenarios:
        scenario['fake_json_dump'] = json.dumps(scenario['test_version_info'])
        scenario['expected_value'] = scenario['test_version_info']

    def test_passes_specified_object(self, mock_func_json_dumps):
        """ Should pass the specified object to `json.dumps`. """
        result = version.serialise_version_info_from_mapping(
                self.test_version_info)
        mock_func_json_dumps.assert_called_with(
                self.test_version_info, indent=mock.ANY)

    def test_returns_expected_result(self, mock_func_json_dumps):
        """ Should return expected result. """
        mock_func_json_dumps.return_value = self.fake_json_dump
        result = version.serialise_version_info_from_mapping(
                self.test_version_info)
        value = json.loads(result)
        self.assertEqual(self.expected_value, value)


@mock.patch.object(version.ChangeLogEntry, 'validate_release_date')
class validate_distutils_release_date_value_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘validate_distutils_release_date_value’ function. """

    scenarios = [
            ('success', {
                'validation_effect': (lambda *args, **kwargs: None),
                'expected_result': None,
                }),
            ('failure', {
                'validation_effect': ValueError("Do not want"),
                'expected_error': distutils.errors.DistutilsSetupError,
                }),
            ]

    def setUp(self):
        """ Set up test fixtures. """
        super(validate_distutils_release_date_value_TestCase, self).setUp()

        self.test_args = {
                'distribution': object(),
                'attrib': self.getUniqueString(),
                'value': self.getUniqueString(),
                }

    def test_returns_expected_result(self, mock_func_validate_release_date):
        """ Should return expected result. """
        mock_func_validate_release_date.side_effect = self.validation_effect
        if hasattr(self, 'expected_error'):
            self.assertRaises(
                    self.expected_error,
                    version.validate_distutils_release_date_value,
                    **self.test_args)
        else:
            result = version.validate_distutils_release_date_value(
                    **self.test_args)
            self.assertEqual(self.expected_result, result)


DistributionMetadata_defaults = {
        name: None
        for name in list(collections.OrderedDict.fromkeys(
            distutils.dist.DistributionMetadata._METHOD_BASENAMES))}
FakeDistributionMetadata = collections.namedtuple(
        'FakeDistributionMetadata', DistributionMetadata_defaults.keys())

Distribution_defaults = {
        'metadata': None,
        'version': None,
        'release_date': None,
        'maintainer': None,
        'maintainer_email': None,
        }
FakeDistribution = collections.namedtuple(
        'FakeDistribution', Distribution_defaults.keys())

def make_fake_distribution(
        fields_override=None, metadata_fields_override=None):
    metadata_fields = DistributionMetadata_defaults.copy()
    if metadata_fields_override is not None:
        metadata_fields.update(metadata_fields_override)
    metadata = FakeDistributionMetadata(**metadata_fields)

    fields = Distribution_defaults.copy()
    fields['metadata'] = metadata
    if fields_override is not None:
        fields.update(fields_override)
    distribution = FakeDistribution(**fields)

    return distribution

@mock.patch.object(
        version.ChangeLogEntry, 'make_ordered_dict',
        new=functools.partial((lambda cls, d: d), version.ChangeLogEntry))
class generate_version_info_from_distribution_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘generate_version_info_from_distribution’ function. """

    scenarios = [
            ('simple', {
                'test_distribution': make_fake_distribution(
                    fields_override={
                        'release_date': "2001-01-01",
                        'maintainer': "Foo Bar",
                        'maintainer_email': "foo.bar@example.org",
                        },
                    metadata_fields_override={
                        'version': "1.0",
                        },
                    ),
                'expected_result': {
                    'version': "1.0",
                    'release_date': "2001-01-01",
                    'maintainer': "Foo Bar <foo.bar@example.org>",
                    'body': "",
                    },
                }),
            ('no maintainer', {
                'test_distribution': make_fake_distribution(
                    fields_override={
                        'release_date': "2001-01-01",
                        },
                    metadata_fields_override={
                        'version': "1.0",
                        },
                    ),
                'expected_result': {
                    'version': "1.0",
                    'release_date': "2001-01-01",
                    'maintainer': "",
                    'body': "",
                    },
                }),
            ('no maintainer name', {
                'test_distribution': make_fake_distribution(
                    fields_override={
                        'release_date': "2001-01-01",
                        'maintainer_email': "foo.bar@example.org",
                        },
                    metadata_fields_override={
                        'version': "1.0",
                        },
                    ),
                'expected_result': {
                    'version': "1.0",
                    'release_date': "2001-01-01",
                    'maintainer': "",
                    'body': "",
                    },
                }),
            ('no maintainer email', {
                'test_distribution': make_fake_distribution(
                    fields_override={
                        'release_date': "2001-01-01",
                        'maintainer': "Foo Bar",
                        },
                    metadata_fields_override={
                        'version': "1.0",
                        },
                    ),
                'expected_result': {
                    'version': "1.0",
                    'release_date': "2001-01-01",
                    'maintainer': "",
                    'body': "",
                    },
                }),
            ]

    def test_returns_expected_result(self):
        """ Should return expected result. """
        result = version.generate_version_info_from_distribution(
                self.test_distribution)
        self.assertEqual(self.expected_result, result)


class get_changelog_path_TestCase(
        testscenarios.WithScenarios, testtools.TestCase):
    """ Test cases for ‘get_changelog_path’ function. """

    default_path = "."
    default_script_filename = "setup.py"

    scenarios = [
            ('simple', {}),
            ('unusual script name', {
                'script_filename': "lorem_ipsum",
                }),
            ('relative script path', {
                'script_directory': "dolor/sit/amet",
                }),
            ('absolute script path', {
                'script_directory': "/dolor/sit/amet",
                }),
            ('specify filename', {
                'changelog_filename': "adipiscing",
                }),
            ]

    def setUp(self):
        """ Set up test fixtures. """
        super(get_changelog_path_TestCase, self).setUp()

        self.test_distribution = mock.MagicMock(distutils.dist.Distribution)

        if not hasattr(self, 'script_directory'):
            self.script_directory = self.default_path
        if not hasattr(self, 'script_filename'):
            self.script_filename = self.default_script_filename
        self.test_distribution.script_name = os.path.join(
                self.script_directory, self.script_filename)

        changelog_filename = version.changelog_filename
        if hasattr(self, 'changelog_filename'):
            changelog_filename = self.changelog_filename

        self.expected_result = os.path.join(
                self.script_directory, changelog_filename)

    def test_returns_expected_result(self):
        """ Should return expected result. """
        args = {
                'distribution': self.test_distribution,
                }
        if hasattr(self, 'changelog_filename'):
            args.update({'filename': self.changelog_filename})
        result = version.get_changelog_path(**args)
        self.assertEqual(self.expected_result, result)


@mock.patch.object(version, 'get_changelog_path')
@mock.patch.object(version, 'generate_version_info_from_changelog')
@mock.patch.object(version, 'serialise_version_info_from_mapping')
class generate_egg_info_metadata_TestCase(testtools.TestCase):
    """ Test cases for ‘generate_egg_info_metadata’ function. """

    def setUp(self):
        """ Set up test fixtures. """
        super(generate_egg_info_metadata_TestCase, self).setUp()

        self.fake_command = mock.MagicMock(name="Command")
        self.fake_outfile_name = self.getUniqueString()
        self.fake_outfile_path = self.getUniqueString()
        self.test_args = {
                'cmd': self.fake_command,
                'outfile_name': self.fake_outfile_name,
                'outfile_path': self.fake_outfile_path,
                }

    def test_gets_changelog_path_from_distribution(
            self,
            mock_func_serialise_version_info,
            mock_func_generate_version_info,
            mock_func_get_changelog_path):
        """ Should get changelog path from specified distribution. """
        version.generate_egg_info_metadata(**self.test_args)
        mock_func_get_changelog_path.assert_called_with(
                self.fake_command.distribution)

    def test_generates_version_info_from_changelog(
            self,
            mock_func_serialise_version_info,
            mock_func_generate_version_info,
            mock_func_get_changelog_path):
        """ Should generate version info from specified changelog. """
        version.generate_egg_info_metadata(**self.test_args)
        expected_changelog_path = mock_func_get_changelog_path.return_value
        mock_func_generate_version_info.assert_called_with(
                expected_changelog_path)

    def test_serialises_version_info_from_mapping(
            self,
            mock_func_serialise_version_info,
            mock_func_generate_version_info,
            mock_func_get_changelog_path):
        """ Should serialise version info from specified mapping. """
        version.generate_egg_info_metadata(**self.test_args)
        expected_version_info = mock_func_generate_version_info.return_value
        mock_func_serialise_version_info.assert_called_with(
                expected_version_info)

    def test_writes_file_using_command_context(
            self,
            mock_func_serialise_version_info,
            mock_func_generate_version_info,
            mock_func_get_changelog_path):
        """ Should write the metadata file using the command context. """
        version.generate_egg_info_metadata(**self.test_args)
        expected_content = mock_func_serialise_version_info.return_value
        self.fake_command.write_file.assert_called_with(
                "version info", self.fake_outfile_path, expected_content)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
