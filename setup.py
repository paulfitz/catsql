#!/usr/bin/env python

from setuptools import setup

setup(name="catsql",
      version="0.1.5",
      author="Paul Fitzpatrick",
      author_email="paulfitz@alum.mit.edu",
      description="Display quick view from sql databases",
      packages=['catsql'],
      entry_points={
          "console_scripts": [
              "catsql=catsql.main:main"
          ]
      },
      install_requires=[
          "SQLAlchemy>=1.0.11",
          "python-magic",
          "unicodecsv"
      ],
      url="https://github.com/paulfitz/catsql"
)
