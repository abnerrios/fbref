# coding: utf-8
from bleach import VERSION
from setuptools import setup, find_packages
NAME = "fbref"
VERSION = "0.0.1"

REQUIRES = ["beautifulsoup4==4.10.0"]

setup(
  name=NAME,
  version=VERSION,
  description="Collect match data from `Fbref`.",
  author_email="abnerrios@yahoo.com",
  keywords=['Football', 'Bet', 'Data Analysis'],
  install_requires=REQUIRES,
  packages=find_packages(),
  include_package_data=True
)