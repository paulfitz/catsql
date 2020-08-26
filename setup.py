#!/usr/bin/env python

import sys
from setuptools import setup

install_requires = [
    "daff >= 1.3.14",
    "openpyxl >= 2.4.1",
    "six >= 1.7.3",
    "SQLAlchemy >= 1.0.11",
    "parsedatetime == 2.5",
]

if sys.version_info[0] == 2:
    install_requires.append('unicodecsv')

setup(name="catsql",
      version="0.4.13",
      author="Paul Fitzpatrick",
      author_email="paulfitz@alum.mit.edu",
      description="Display a quick view of sql databases (and make quick edits)",
      packages=['catsql', 'catsql.daffsql'],
      entry_points={
          "console_scripts": [
              "catsql=catsql.main:main",
              "patchsql=catsql.patch:main"
          ]
      },
      install_requires=install_requires,
      extras_require={
          "postgres": [
              "psycopg2"
          ],
          "mysql": [
              "mysqlclient"
          ]
      },
      tests_require=[
          'mock',
          'nose'
      ],
      test_suite="nose.collector",
      url="https://github.com/paulfitz/catsql"
)
