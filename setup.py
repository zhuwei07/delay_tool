#!/usr/bin/env python
# -*- coding:utf-8 -*-

from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

setup(
    options={'py2exe': {'bundle_files': 2, 'compressed': True}},
    windows=[{'script': "Main.py"}],
    zipfile=None,
)
