#!/usr/bin/env python

import os
import sys
from setuptools import setup

version = open("__version__.py", "r").read().strip()
# TODO: break on version <3.8.0
setup(
    name="pubpublica",
    version=version,
    description="",
    author="Jens Christian Jensen",
    author_email="jensecj@gmail.com",
    url="http://github.com/pubpublica/pubpublica",
    packages=["pubpublica"],
)
