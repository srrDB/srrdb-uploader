#!/bin/bash
# Just change the username and password variables and launch with ./srrup.sh <srr file> 

# Changes necessary to make this script up to date:
# I just changed http://www.srrdb.com/login.php to http://www.srrdb.com/account/login, 
# and removed the .php from http://www.srrdb.com/upload.php
# I also removed the ! from login=Login! but not sure if that was necessary
# the reasons in the script might needed updating too. 
# I think it now says something like "is a dupe and will be checked by an administrator"
# I just had mine dump out the entire html and check it manually :)

username=""
password=""

messages="was added|already exist|is not an srr file|contains illegal characters|is too large to be extracted|is a 0 byte file|is a folder|is too large to be uploaded"

cookie_jar="/tmp/srrdb_cookie.$username"

curl --cookie-jar "$cookie_jar" \
     --data "login=Login!&password=$password&username=$username" \
     http://www.srrdb.com/login.php > /dev/null 2>&1

for file in $@
do
  post_result="$(curl --cookie $cookie_jar --form "file=@$file" --form "upload=Upload" \
    http://www.srrdb.com/upload.php 2> /dev/null | grep -Eo "$messages")"

  echo ${file%.srr} $post_result.
done

rm -f "$cookie_jar"
