# -*- coding: utf-8 -*-

# setup.py
# Part of ‘python-daemon’, an implementation of PEP 3143.
#
# Copyright © 2008–2011 Ben Finney <ben+python@benfinney.id.au>
# Copyright © 2008 Robert Niederreiter, Jens Klein
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3 of that license or any later version.
# No warranty expressed or implied. See the file LICENSE.GPL-2 for details.

""" Distribution setup for ‘python-daemon’ library.
    """

from __future__ import unicode_literals

import textwrap
from setuptools import setup, find_packages

distribution_name = "python-daemon"
main_module_name = 'daemon'
main_module = __import__(main_module_name, fromlist=[b'version'])
version = main_module.version


def get_descriptions_from_docstring(docstring):
    """ Get package description text from a docstring.

        :param docstring: A docstring formatted conformant with PEP 257.
        :return: A two-item tuple of (`synopsis`, `long_description`). If
            the docstring contains only a single line, `long_description`
            will be ``None``.

        Important implications of PEP 257 convention:

        * The docstring either has only a synopsis (a single line of text),
          or a synopsis and a long description.

        * The synopsis is the first line (only) of the docstring. It may be
          preceded by a blank line if the docstring has a synopsis and long
          description.

        * Leading and trailing whitespace is not part of the synopsis nor
          long description.

        * If the docstring has a long description:

          * The second line of the docstring is blank, separating the
            synopsis from the long description.

          * The long description starts after the blank separator line, and
            extends to the end of the docstring.

          * Common leading whitespace on all the long description lines is
            removed.

        """
    synopsis = None
    long_description = None

    lines = docstring.expandtabs().strip().splitlines()
    if len(lines) < 2:
        synopsis = lines[0].strip()
    else:
        if lines[1].strip():
            raise ValueError(
                "PEP 257 multi-line docstrings must have second line blank")
        synopsis = lines[0].strip()
        long_description = textwrap.dedent("\n".join(lines[2:]))

    return (synopsis, long_description)


description_translate_map = {
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    }

synopsis, long_description = get_descriptions_from_docstring(
        main_module.__doc__)
short_description, long_description = (
    (synopsis.translate(description_translate_map),
     long_description.translate(description_translate_map)))


setup(
    name=distribution_name,
    version=version.version,
    packages=find_packages(exclude=["test"]),

    # setuptools metadata
    zip_safe=False,
    test_suite="test.suite",
    tests_require=[
        "MiniMock >=1.2.2",
        ],
    install_requires=[
        "setuptools",
        "lockfile >=0.9",
        ],

    # PyPI metadata
    author=version.author_name,
    author_email=version.author_email,
    description=short_description,
    license=version.license,
    keywords="daemon fork unix".split(),
    url=main_module._url,
    long_description=long_description,
    classifiers=[
        # Reference: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Python Software Foundation License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
