#!/bin/bash
# Put your Pixiv Username in by replacing $PIXIV_NAME
# The same for your password in $PIXIV_PASS
# Do not put a space between the keyword, the = sign, and your stuff.

# If say, you cancel or something breaks on the like, 50th image, you can restart your download.
# Navigate to the last time that you DIDN'T DOWNLOAD SUCCESSFULLY and make that the first link in
# pixivdl.txt. Then, run this script like usual but with the number of the bad image. So in this
# example, you got 1-49 A-OK, but 50 failed. Well, type "sh pixiv.sh 50" and hit enter and it'll
# start numbering from 50.
if [ ! -z ${1} ]; then
	APPEND=" -j ${1}"
fi

PIXIV_NAME=$PIXIV_NAME PIXIV_PASS=$PIXIV_PASS python ~/host/git/puruselenium/pururinparser.py -m -t 1 -l -e ~/host/downloads -o ~/host/pixivdl.txt ${APPEND}