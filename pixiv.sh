#!/bin/bash
# Put your Pixiv Username in by replacing $PIXIV_NAME
# The same for your password in $PIXIV_PASS
# Do not put a space between the keyword, the = sign, and your stuff.
PIXIV_NAME=$PIXIV_NAME PIXIV_PASS=$PIXIV_PASS python ~/host/git/puruselenium/pururinparser.py -m -t 1 -l -e ~/host/downloads -o ~/host/pixivdl.txt