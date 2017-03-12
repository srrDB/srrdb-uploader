#!/usr/bin/env python3

import sys
import os
import argparse

import requests

username = ""
password = ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="+")
    args = parser.parse_args()
    site = "https://www.srrdb.com/"
    s = requests.session()
    s.post(site + "account/login", data={"username": username, "password": password}) 
    if not "uid" in s.cookies:
        print("Login failed")
        sys.exit(1)
    for f in args.file:
        with open(f, "rb") as fh:
            r = s.post(
                    site + "release/upload",
                    files={"files[]": (os.path.basename(f), fh)},
                    headers={"X-Requested-With": "XMLHttpRequest"}
            )
        msg = r.json()["files"][0]["message"]
        print(msg)
        if r.json()["files"][0]["color"] == 0:
            print("Upload failed")
            sys.exit(1)