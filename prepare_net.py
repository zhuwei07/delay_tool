#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os

libs = {"mathplotlib", "pandas", "openpyxl"}
try:
    for lib in libs:
        os.system("pip install" + lib)
    print("Successful")
except:
    print("Failed pip install")