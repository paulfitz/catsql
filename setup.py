#!/usr/bin/env python

from setuptools import setup

setup(name="catsql",
      version="0.1.6",
      author="Paul Fitzpatrick",
      author_email="paulfitz@alum.mit.edu",
      description="Display quick view from sql databases",
      packages=['catsql', 'catsql.daffsql'],
      entry_points={
          "console_scripts": [
              "catsql=catsql.main:main",
              "patchsql=catsql.patch:main"
          ]
      },
      install_requires=[
          "SQLAlchemy>=1.0.11",
          "python-magic",
          "unicodecsv",
	  "daff",
	  "psycopg2"
      ],
      url="https://github.com/paulfitz/catsql"
)
