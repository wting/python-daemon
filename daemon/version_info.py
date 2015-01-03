# -*- coding: utf-8 -*-

# daemon/version_info.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2014 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Apache License, version 2.0 as published by the
# Apache Software Foundation.
# No warranty expressed or implied. See the file ‘LICENSE.ASF-2’ for details.

""" Distribution version info parsed from reStructuredText. """

from __future__ import (absolute_import, unicode_literals)

import os
import os.path
import json
import datetime
import textwrap
import functools
import collections

try:
    # Python 2 has both ‘str’ (bytes) and ‘unicode’.
    unicode
except NameError:
    # Python 3 names the Unicode data type ‘str’.
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


class NewsEntry:
    """ An individual entry from the ‘NEWS’ document. """

    __metaclass__ = type

    field_names = [
            'released',
            'version',
            'maintainer',
            'body',
            ]

    def __init__(
            self, released=None, version=None, maintainer=None, body=None):
        self.released = released
        self.version = version
        self.maintainer = maintainer
        self.body = body

    @classmethod
    def make_ordered_dict(cls, fields):
        """ Make an ordered dict of the fields. """
        result = collections.OrderedDict(
                (name, fields[name])
                for name in cls.field_names)
        return result

    def as_version_info_entry(self):
        """ Format the news entry as a version info entry. """
        fields = vars(self)
        fields['released'] = self.released.strftime("%Y-%m-%d")
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
    """ Raised when the document is not a valid NEWS document. """


def news_timestamp_to_datetime(text):
    """ Return a datetime value from the news entry timestamp. """
    if text == "FUTURE":
        timestamp = datetime.datetime.max
    else:
        timestamp = datetime.datetime.strptime(text, "%Y-%m-%d")
    return timestamp


class VersionInfoTranslator(docutils.nodes.SparseNodeVisitor):
    """ Translator from document nodes to a version info stream. """

    wrap_width = 78
    bullet_text = "* "

    field_convert_funcs = {
            'released': news_timestamp_to_datetime,
            'maintainer': unicode,
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
        convert_func = self.field_convert_funcs[self.current_field_name]
        attr_name = self.current_field_name
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
        self.current_entry = NewsEntry()

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
def get_generated_version_info_content(infile_path):
    """ Get the version-info stream generated from the changelog.

        :param infile_path: Filesystem path to the input changelog file.
        :return: The generated version info, serialised for output; or
            ``None`` if the file cannot be read.

        """
    content = None
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
        latest_version = get_latest_version(versions_all)
        content = json.dumps(latest_version, indent=4)

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


def update_version_info_file_if_needed(outfile_path, changelog_file_path):
    """ Update the version-info file iff it is out of date.

        :param outfile_path: Filesystem path to the version-info file.
        :param changelog_file_path: Filesystem path to the changelog.
        :return: ``None``.

        """
    generated_content = get_generated_version_info_content(changelog_file_path)
    existing_content = get_existing_version_info_content(outfile_path)

    if generated_content is not None:
        if generated_content != existing_content:
            version_info_file = open(outfile_path, 'w+t')
            version_info_file.write(generated_content)
            version_info_file.close()


def get_latest_version(version_info):
    """ Get the latest version from a version-info stream.

        :param version_info: A sequence of mappings for changelog entries.
        :return: The latest version, as an ordered mapping of fields.

        """
    versions_by_release_date = {
            item['released']: item
            for item in version_info}
    latest_release_date = max(versions_by_release_date.keys())
    version = NewsEntry.make_ordered_dict(
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
