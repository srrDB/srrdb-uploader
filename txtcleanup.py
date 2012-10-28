#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

""" Cleans up txt files created with the following DOS script: 
http://pastebin.com/xzxuGzFT

It's included in the srrdb upload script now.

@ECHO OFF
goto start

:srs
SET gx=%1
srs %gx% > %gx%.txt
IF EXIST "%gx:~0,-4%.srs" del %gx%.txt
cd..
goto end

:run
SET gx=%1
echo %gx%
cd %gx%
FOR /F "usebackq tokens=*" %%G IN (`dir /B *.avi *.mkv`) DO CALL :srs %%G
goto end

:start
FOR /F "usebackq tokens=*" %%G IN (`dir /A:D /B`) DO CALL :run %%G

:end
---
newer version?
@ECHO OFF
goto start

:srs
SET gx=%1
SET onlyfile=%gx:~1,-5%
SET extension=%gx:~-4,-1%
echo %gx%
echo %onlyfile%
echo %extension%
echo %onlyfile%.%extension%.txt
srs %gx% > %onlyfile%.%extension%.txt
IF EXIST %onlyfile%.srs del "%onlyfile%.%extension%.txt"
goto end

:run
SET gx=%1
echo %gx%
cd %gx%
FOR /F "usebackq tokens=*" %%G IN (`dir /B *.avi *.mkv`) DO CALL :srs "%%G"
cd..
goto end

:start
FOR /F "usebackq tokens=*" %%G IN (`dir /A:D /B`) DO CALL :run %%G

:end
---
@ECHO OFF
goto start
pause

:srs
SET gx=%1
SET filename=%gx:~1,-5%
SET extension=%gx:~-4,-1%
FOR %%T in (%gx%) DO SET path=%%~pT
C:\WINDOWS\system32\srs.exe %gx% -o %path% > "%filename%.%extension%.txt"
IF EXIST "%filename%.srs" del "%filename%.%extension%.txt"
echo Done %gx%
goto end

:start
FOR /F "usebackq tokens=*" %%G IN (`dir /A:-D /B /S *.avi *.mkv`) DO CALL :srs "%%G"

:end

"""

from __future__ import unicode_literals
import optparse
import sys
import os
import re
import glob
import codecs

def fix_txt(filename):
    if options.dry_run:
        print("Fixing '%s'." % filename)
        return
    data = codecs.open(filename, encoding="latin-1", mode="r").read()
    newdata = re.sub(".*Corruption", "Corruption", data)
    newdata = newdata.replace("\xff", ".") # cp850 \xa0
    newdata = newdata.replace("\xa0", ".")
    newdata = re.sub("\r(?!\n)|(?<!\r)\n", "\r\n", newdata)
    if newdata != data:
        print(filename)
        f = open(filename, "wb")
        f.write(newdata)
        f.close()
    else:
        print("Nothing done for %s!" % filename)

def main(options, args):
    for element in args:
        element = os.path.abspath(element)
        if os.path.isfile(element) and element[-4:] == ".txt":
            fix_txt(element)
        elif os.path.isdir(element):
            for tfile in glob.iglob("*.txt"):
                fix_txt(tfile)
            for tfile in glob.iglob("*/*.txt"):
                fix_txt(tfile)
        else:
            print("WTF are you supplying me?")
            
if __name__ == '__main__':
    parser = optparse.OptionParser(
        usage="Usage: %prog [txt files] [directories] [options]'\n"
        "This tool will clean up all generated .avi/mkv.txt files.\n",
        version="%prog 0.1 (2011-11-05)") # --help, --version
    
    parser.add_option("-n", "--dry-run", help="do no harm",
                      action="store_true", dest="dry_run", default=False)
    
    # no arguments given
    if len(sys.argv) < 2:
        print(parser.format_help())
    else:
        (options, args) = parser.parse_args()
        main(options, args)
        