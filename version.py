# -*- coding: utf-8 -*-

# version.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
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

try:
    # Python 2 has both ‘str’ (bytes) and ‘unicode’.
    basestring = basestring
    unicode = unicode
except NameError:
    # Python 3 names the Unicode data type ‘str’.
    basestring = str
    unicode = str

from docutils.core import publish_string
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


def changelog_timestamp_to_datetime(text):
    """ Return a datetime value from the changelog entry timestamp. """
    if text == "FUTURE":
        timestamp = datetime.datetime.max
    else:
        timestamp = datetime.datetime.strptime(
                text, ChangeLogEntry.date_format)
    return timestamp


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

    def depart_comment(self, node):
        pass

    def visit_field_body(self, node):
        (attr_name, convert_func) = self.attr_convert_funcs_by_attr_name[
                self.current_field_name]
        attr_value = convert_func(node.astext())
        setattr(self.current_entry, attr_name, attr_value)
        raise docutils.nodes.SkipNode

    def depart_field_body(self, node):
        pass

    def visit_field_list(self, node):
        section_node = node.parent
        if not isinstance(section_node, docutils.nodes.section):
            raise InvalidFormatError(
                    "Unexpected field list within {node!r}".format(
                        node=section_node))

    def depart_field_list(self, node):
        self.current_field_name = None
        if self.current_entry is not None:
            self.current_entry.body = ""

    def visit_field_name(self, node):
        field_name = node.astext()
        if field_name.lower() not in ["released", "maintainer"]:
            raise InvalidFormatError(
                    "Unexpected field name {name!r}".format(name=field_name))
        self.current_field_name = field_name.lower()
        raise docutils.nodes.SkipNode

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
        self.current_entry = ChangeLogEntry()

    def depart_section(self, node):
        self.content.append(
                self.current_entry.as_version_info_entry())
        self.current_entry = None

    def visit_title(self, node):
        section_node = node.parent
        if not isinstance(section_node, docutils.nodes.section):
            raise docutils.nodes.SkipNode(
                    "Only section titles are processed for version info")

    def depart_title(self, node):
        title_text = node.astext()
        words = title_text.split(" ")
        version = None
        if len(words) == 2:
            if words[0].lower() in ["version"]:
                version = words[-1]
        if version is None:
            raise InvalidFormatError(
                    "Unexpected title text {text!r}".format(text=title_text))
        self.current_entry.version = version


try:
    lru_cache = functools.lru_cache
except AttributeError:
    # Python < 3.2 does not have the `functools.lru_cache` function.
    # Not essential, so replace it with a no-op.
    lru_cache = lambda maxsize=None, typed=False: lambda func: func


@lru_cache(maxsize=128)
def generate_version_info_from_changelog(infile_path):
    """ Get the version-info stream generated from the changelog.

        :param infile_path: Filesystem path to the input changelog file.
        :return: The generated version info mapping; or ``None`` if the
            file cannot be read.

        """
    version_info = collections.OrderedDict()
    infile_content = None

    try:
        with open(infile_path, 'rt') as infile:
            infile_content = infile.read()
    except IOError:
        pass

    if infile_content is not None:
        versions_all_json = publish_string(
                infile_content, writer=VersionInfoWriter())
        versions_all = json.loads(versions_all_json.decode('utf-8'))
        version_info = get_latest_version(versions_all)

    return version_info


def serialise_version_info_from_mapping(version_info):
    """ Generate the version info serialised data.

        :param version_info: Mapping of version info items.
        :return: The version info serialised to JSON.

        """
    content = json.dumps(version_info, indent=4)

    return content


@lru_cache(maxsize=128)
def get_existing_version_info_content(infile_path):
    """ Get the content of the existing version-info file.

        :param infile_path: Filesystem path to the input version-info file.
        :return: The content of the input file, or ``None`` if the
            file cannot be read.

        """
    content = None

    try:
        with open(infile_path, 'rt') as infile:
            content = infile.read()
    except IOError:
        pass

    return content


def is_source_file_newer(source_path, destination_path, force=False):
    """ Return True if destination is older than source or does not exist.

        :param source_path: Filesystem path to the source file.
        :param destination_path: Filesystem path to the destination file.
        :param force: If true, return ``True`` without examining files.

        :return: ``False`` iff the age of the destination file (if it
            exists) is no older than the age of the source file.

        A file's age is determined from its content modification
        timestamp in the filesystem.

        """
    result = True
    if not force:
        source_stat = os.stat(source_path)
        source_mtime = source_stat.st_mtime
        try:
            destination_stat = os.stat(destination_path)
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                destination_mtime = None
            else:
                raise
        else:
            destination_mtime = destination_stat.st_mtime
        if destination_mtime is not None:
            result = (source_mtime > destination_mtime)

    return result


def generate_version_info_file(outfile_path, changelog_file_path):
    """ Generate the version-info file from the changelog.

        :param outfile_path: Filesystem path to the version-info file.
        :param changelog_file_path: Filesystem path to the changelog.
        :return: ``None``.

        """
    generated_content = get_generated_version_info_content(changelog_file_path)
    existing_content = get_existing_version_info_content(outfile_path)

    if generated_content is not None:
        version_info_file = open(outfile_path, 'w+t')
        version_info_file.write(generated_content)
        version_info_file.close()


rfc822_person_regex = re.compile(
        "^(?P<name>[^<]+) <(?P<email>[^>]+)>$")

@lru_cache(maxsize=128)
def parse_person_field(value):
    """ Parse a person field into name and email address. """
    result = (None, None)

    match = rfc822_person_regex.match(value)
    if match is not None:
        result = (match.name, match.email)

    return result    


@lru_cache(maxsize=128)
def validate_distutils_release_date_value(distribution, attrib, value):
    """ Validate the ‘release_date’ parameter value. """
    try:
        ChangeLogEntry.validate_release_date(value)
    except ValueError as exc:
        raise distutils.DistutilsSetupError(
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
    """ Setuptools entry point to generate version info metadata. """
    version_info = generate_version_info_from_distribution(cmd.distribution)
    content = serialise_version_info_from_mapping(version_info)
    cmd.write_file("version info", outfile_path, content)


def get_latest_version(version_info):
    """ Get the latest version from a version-info stream.

        :param version_info: A sequence of mappings for changelog entries.
        :return: The latest version, as an ordered mapping of fields.

        """
    versions_by_release_date = {
            item['release_date']: item
            for item in version_info}
    latest_release_date = max(versions_by_release_date.keys())
    version = ChangeLogEntry.make_ordered_dict(
            versions_by_release_date[latest_release_date])
    return version


@lru_cache(maxsize=128)
def read_version_info_from_file(infile_path):
    """ Read the version info from the specified file.

        :param infile_path: Filesystem path to the version-info file.
        :return: The version info mapping for the recorded version.

        The version info file contains a JSON-serialised rendering of
        the changelog entry for the distribution from which the
        package was built.

        """
    result = None

    infile_content = get_existing_version_info_content(infile_path)
    if infile_content is not None:
        result = json.loads(infile_content)

    return result


# Local variables:
# coding: utf-8
# mode: python
# End:
# vim: fileencoding=utf-8 filetype=python :
