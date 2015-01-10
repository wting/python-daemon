# -*- coding: utf-8 -*-

# version.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2015 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3 of that license or any later version.
# No warranty expressed or implied. See the file ‘LICENSE.GPL-3’ for details.

""" Version information unified for human- and machine-readable formats.

    The project ‘ChangeLog’ file is a reStructuredText document, with
    each section describing a version of the project. The document is
    intended to be readable as-is by end users.

    This module handles transformation from the ‘ChangeLog’ to a
    mapping of version information, serialised as JSON. It also
    provides functionality for Distutils to use this information.

    Requires:

    * Docutils <http://docutils.sourceforge.net/>
    * JSON <https://docs.python.org/3/reference/json.html>

    """

from __future__ import (absolute_import, unicode_literals)

import os
import errno
import json
import datetime
import textwrap
import re
import functools
import collections
import distutils
import distutils.errors
try:
    # Python 2 has both ‘str’ (bytes) and ‘unicode’ (text).
    basestring = basestring
    unicode = unicode
except NameError:
    # Python 3 names the Unicode data type ‘str’.
    basestring = str
    unicode = str

import docutils.core
import docutils.nodes
import docutils.writers


class VersionInfoWriter(docutils.writers.Writer, object):
    """ Docutils writer to produce a version info JSON data stream.
        """

    __metaclass__ = type

    supported = ['version_info']
    """ Formats this writer supports. """

    def __init__(self):
        super(VersionInfoWriter, self).__init__()
        self.translator_class = VersionInfoTranslator

    def translate(self):
        visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class ChangeLogEntry:
    """ An individual entry from the ‘ChangeLog’ document. """

    __metaclass__ = type

    field_names = [
            'release_date',
            'version',
            'maintainer',
            'body',
            ]

    date_format = "%Y-%m-%d"
    default_version = "UNKNOWN"
    default_release_date = "UNKNOWN"

    def __init__(
            self,
            release_date=default_release_date, version=default_version,
            maintainer=None, body=None):
        self.validate_release_date(release_date)
        self.release_date = release_date

        self.version = version

        self.validate_maintainer(maintainer)
        self.maintainer = maintainer
        self.body = body

    @classmethod
    def validate_release_date(cls, value):
        """ Validate the `release_date` value.

            :param value: The prospective `release_date` value.
            :return: ``None`` if the value is valid.
            :raises ValueError: If the value is invalid.

            """
        if value in ["UNKNOWN", "FUTURE"]:
            # A valid non-date value.
            return None

        # Raises `ValueError` if parse fails.
        datetime.datetime.strptime(value, ChangeLogEntry.date_format)

    @classmethod
    def validate_maintainer(cls, value):
        """ Validate the `maintainer` value.

            :param value: The prospective `maintainer` value.
            :return: ``None`` if the value is valid.
            :raises ValueError: If the value is invalid.

            """
        valid = False

        if value is None:
            valid = True
        elif rfc822_person_regex.search(value):
            valid = True

        if not valid:
            raise ValueError("Not a valid person specification {value!r}")
        else:
            return None

    @classmethod
    def make_ordered_dict(cls, fields):
        """ Make an ordered dict of the fields. """
        result = collections.OrderedDict(
                (name, fields[name])
                for name in cls.field_names)
        return result

    def as_version_info_entry(self):
        """ Format the changelog entry as a version info entry. """
        fields = vars(self)
        entry = self.make_ordered_dict(fields)

        return entry


def get_name_for_field_body(node):
    """ Return the text of the field name of a field body node. """
    field_node = node.parent
    field_name_node_index = field_node.first_child_matching_class(
            docutils.nodes.field_name)
    field_name_node = field_node.children[field_name_node_index]
    field_name = unicode(field_name_node.children[0])
    return field_name


class InvalidFormatError(ValueError):
    """ Raised when the document is not a valid ‘ChangeLog’ document. """


class VersionInfoTranslator(docutils.nodes.SparseNodeVisitor):
    """ Translator from document nodes to a version info stream. """

    wrap_width = 78
    bullet_text = "* "

    attr_convert_funcs_by_attr_name = {
            'released': ('release_date', unicode),
            'version': ('version', unicode),
            'maintainer': ('maintainer', unicode),
            }

    def __init__(self, document):
        docutils.nodes.NodeVisitor.__init__(self, document)
        self.settings = document.settings
        self.current_section_level = 0
        self.current_field_name = None
        self.content = []
        self.indent_width = 0
        self.initial_indent = ""
        self.subsequent_indent = ""
        self.current_entry = None

    def astext(self):
        """ Return the translated document as text. """
        text = json.dumps(self.content, indent=4)
        return text

    def append_to_current_entry(self, text):
        if self.current_entry is not None:
            if self.current_entry.body is not None:
                self.current_entry.body += text

    def visit_Text(self, node):
        raw_text = node.astext()
        text = textwrap.fill(
                raw_text,
                width=self.wrap_width,
                initial_indent=self.initial_indent,
                subsequent_indent=self.subsequent_indent)
        self.append_to_current_entry(text)

    def depart_Text(self, node):
        pass

    def visit_comment(self, node):
        raise docutils.nodes.SkipNode

    def visit_field_body(self, node):
        field_list_node = node.parent.parent
        if not isinstance(field_list_node, docutils.nodes.field_list):
            raise InvalidFormatError(
                    "Unexpected field within {node!r}".format(
                        node=field_list_node))
        (attr_name, convert_func) = self.attr_convert_funcs_by_attr_name[
                self.current_field_name]
        attr_value = convert_func(node.astext())
        setattr(self.current_entry, attr_name, attr_value)

    def depart_field_body(self, node):
        pass

    def visit_field_list(self, node):
        pass

    def depart_field_list(self, node):
        self.current_field_name = None
        self.current_entry.body = ""

    def visit_field_name(self, node):
        field_name = node.astext()
        if self.current_section_level == 1:
            # At a top-level section.
            if field_name.lower() not in ["released", "maintainer"]:
                raise InvalidFormatError(
                        "Unexpected field name {name!r}".format(name=field_name))
            self.current_field_name = field_name.lower()

    def depart_field_name(self, node):
        pass

    def visit_bullet_list(self, node):
        self.current_context = []

    def depart_bullet_list(self, node):
        self.current_entry.changes = self.current_context
        self.current_context = None

    def adjust_indent_width(self, delta):
        self.indent_width += delta
        self.subsequent_indent = " " * self.indent_width
        self.initial_indent = self.subsequent_indent

    def visit_list_item(self, node):
        indent_delta = +len(self.bullet_text)
        self.adjust_indent_width(indent_delta)
        self.initial_indent = self.subsequent_indent[:-indent_delta]
        self.append_to_current_entry(self.initial_indent + self.bullet_text)

    def depart_list_item(self, node):
        indent_delta = +len(self.bullet_text)
        self.adjust_indent_width(-indent_delta)
        self.append_to_current_entry("\n")

    def visit_section(self, node):
        self.current_section_level += 1
        if self.current_section_level == 1:
            # At a top-level section.
            self.current_entry = ChangeLogEntry()
        else:
            raise InvalidFormatError(
                    "Subsections not implemented for this writer")

    def depart_section(self, node):
        self.current_section_level -= 1
        self.content.append(
                self.current_entry.as_version_info_entry())
        self.current_entry = None

    _expected_title_word_length = len("Version FOO".split(" "))

    def depart_title(self, node):
        title_text = node.astext()
        # At a top-level section.
        words = title_text.split(" ")
        version = None
        if len(words) != self._expected_title_word_length:
            raise InvalidFormatError(
                    "Unexpected title text {text!r}".format(text=title_text))
        if words[0].lower() not in ["version"]:
            raise InvalidFormatError(
                    "Unexpected title text {text!r}".format(text=title_text))
        version = words[-1]
        self.current_entry.version = version


def changelog_to_version_info_collection(infile, writer):
    """ Render the ‘ChangeLog’ document to a version info collection.

        :param infile: A file-like object containing the changelog.
        :param writer: A Docutils writer to render to JSON version
            info format.
        :return: The serialised JSON data of the version info collection.

        """
    settings_overrides = {
            'doctitle_xform': False,
            }
    version_info_json = docutils.core.publish_string(
            infile.read(), writer=writer,
            settings_overrides=settings_overrides)

    return version_info_json


try:
    lru_cache = functools.lru_cache
except AttributeError:
    # Python < 3.2 does not have the `functools.lru_cache` function.
    # Not essential, so replace it with a no-op.
    lru_cache = lambda maxsize=None, typed=False: lambda func: func


@lru_cache(maxsize=128)
def generate_version_info_from_changelog(infile_path):
    """ Get the version info for the latest version in the changelog.

        :param infile_path: Filesystem path to the input changelog file.
        :return: The generated version info mapping; or ``None`` if the
            file cannot be read.

        """
    version_info = collections.OrderedDict()

    writer = VersionInfoWriter()
    versions_all_json = None
    try:
        with open(infile_path, 'rt') as infile:
            versions_all_json = changelog_to_version_info_collection(
                    infile, writer=writer)
    except OSError:
        # If we can't read the input file, leave the collection empty.
        pass

    if versions_all_json is not None:
        versions_all = json.loads(versions_all_json.decode('utf-8'))
        version_info = get_latest_version(versions_all)

    return version_info


def get_latest_version(versions):
    """ Get the latest version from a collection of changelog entries.

        :param versions: A collection of mappings for changelog entries.
        :return: An ordered mapping of fields for the latest version,
            if `versions` is non-empty; otherwise, an empty mapping.

        """
    version_info = collections.OrderedDict()

    versions_by_release_date = {
            item['release_date']: item
            for item in versions}
    if versions_by_release_date:
        latest_release_date = max(versions_by_release_date.keys())
        version_info = ChangeLogEntry.make_ordered_dict(
                versions_by_release_date[latest_release_date])

    return version_info


def serialise_version_info_from_mapping(version_info):
    """ Generate the version info serialised data.

        :param version_info: Mapping of version info items.
        :return: The version info serialised to JSON.

        """
    content = json.dumps(version_info, indent=4)

    return content


rfc822_person_regex = re.compile(
        "^(?P<name>[^<]+) <(?P<email>[^>]+)>$")

ParsedPerson = collections.namedtuple('ParsedPerson', ['name', 'email'])

@lru_cache(maxsize=128)
def parse_person_field(value):
    """ Parse a person field into name and email address.

        :param value: The text value specifying a person.
        :return: A 2-tuple (name, email) for the person's details.

        If the `value` does not match a standard person with email
        address, the `email` item is ``None``.

        """
    result = (None, None)

    match = rfc822_person_regex.match(value)
    if len(value):
        if match is not None:
            result = ParsedPerson(
                    name=match.group('name'),
                    email=match.group('email'))
        else:
            result = ParsedPerson(name=value, email=None)

    return result    


@lru_cache(maxsize=128)
def validate_distutils_release_date_value(distribution, attrib, value):
    """ Validate the ‘release_date’ parameter value.

        :param distribution: The Distutils distribution context.
        :param attrib: The attribute for the value.
        :param value: The value to be validated.
        :return: ``None`` if the value is valid for the atribute.
        :raises distutils.DistutilsSetupError: If the value is invalid
            for the attribute.

        This function is designed to be called as a Distutils entry
        point for ‘distutils.setup_keywords’. This allows the addition
        of a ‘release_date’ parameter to ‘setup’.

        """
    try:
        ChangeLogEntry.validate_release_date(value)
    except ValueError as exc:
        raise distutils.errors.DistutilsSetupError(
                "{attrib!r} must be a valid release date"
                " (got {value!r}".format(
                    attrib=attrib, value=value))


@lru_cache(maxsize=128)
def generate_version_info_from_distribution(distribution):
    """ Generate a version info mapping from a Setuptools distribution. """
    if all(
            getattr(distribution, attr_name)
            for attr_name in ['maintainer', 'maintainer_email']):
        maintainer_text = "{name} <{email}>".format(
                name=distribution.maintainer,
                email=distribution.maintainer_email)
    else:
        maintainer_text = ""

    result = ChangeLogEntry.make_ordered_dict({
            'version': distribution.version,
            'release_date': distribution.release_date,
            'maintainer': maintainer_text,
            'body': "",
            })

    return result


def generate_egg_info_metadata(cmd, outfile_name, outfile_path):
    """ Setuptools entry point to generate version info metadata.

        :param cmd: The Distutils command context.
        :param outfile_name: Filename for the metadata file.
        :param outfile_path: Filesystem path for the metadata file.

        This function is designed to be called as a Setuptools entry
        point for ‘egg_info.writers’. This allows the creation of the
        metadata file during build.

        """
    version_info = generate_version_info_from_distribution(cmd.distribution)
    content = serialise_version_info_from_mapping(version_info)
    cmd.write_file("version info", outfile_path, content)


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
