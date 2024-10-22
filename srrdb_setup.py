#!/usr/bin/env python
# -*- coding: latin-1 -*-

from distutils.core import setup
import py2exe
import sys
import srrdb

sys.argv.append('py2exe')

setup(
    # The first three parameters are not required, if at least a
    # 'version' is given, then a versioninfo resource is built from
    # them and added to the executables.
    options = {'py2exe': {'bundle_files': 1, 'compressed': True}},
    version = srrdb.__version__,
    description = srrdb._USER_AGENT,
    name = "srrdb",
    zipfile = None,

    # targets to build
    console = ["srrdb.py", "txtcleanup.py"],
    )
