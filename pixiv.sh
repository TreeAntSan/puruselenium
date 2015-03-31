#!/bin/bash
# Put your Pixiv Username in by replacing $PIXIV_NAME
# The same for your password in $PIXIV_PASS
# Do not put a space between the keyword, the = sign, and your stuff.


# JUMP - FIRST SYSTEM of download resuming using DL Links
# Okay, if your download breaks or it for some reason quits early, here is how to fix it with input.
# In your pixiv DL list say your download breaks on the 28th image
# Go back to your artist's works collection, and since there are 20 works per page, navigate to
# page 2 (works 21-40)
# Copy the link and enter it as a replacement for the original download link.
# Now, since we're restarting with the 28th work, add ">>28" to the end of the link.
# Since the 28th image is the 8th image on the second page, add "<<8"
# If it was the 64th, you'd get the 4th link (showing 61-80) and write ">>64<<4"
# That's at the end of the link. If for some reason you only want to start counting at a certain work
# item (you just don't like their first 4 things I guess?) then you just just write "<<5" and
# it'll start DL'ing with the 5th work on the works page you link, naming it #1 and so on.
# Restart the DL and you'll be good!


# If say, you cancel or something breaks on the like, 50th image, you can restart your download.
# Navigate to the last time that you DIDN'T DOWNLOAD SUCCESSFULLY and make that the first link in
# pixivdl.txt. Then, run this script like usual but with the number of the bad image. So in this
# example, you got 1-49 A-OK, but 50 failed. Well, type
# 	sh pixiv.sh 50
# and hit enter and it'll start numbering from 50.
if [ ! -z ${1} ]; then
	APPEND=" -j ${1}"
fi

# If it broke in the middle of a tagged search you'll need to restart from the works page with
# your tag selected. So add a second argument with the tagged work page (page 1, page 2, etc)
# and write the # it is on the page.
if [ ! -z ${2} ]; then
	APPEND="${APPEND} -f ${2}"
fi



# Finally, Pixiv is a pretty heavy website. It needs to load TONS of stuff from all over. So
# if a page stops loading, you should just try selecting the address bar and hitting the return
# key. I should get it to start going again. WebDriver won't continue unless every dumb thing is
# loaded completely, and that includes slow ads.

PIXIV_NAME=$PIXIV_NAME PIXIV_PASS=$PIXIV_PASS python ~/host/git/puruselenium/pururinparser.py -m -t 1 -l -e ~/host/downloads -o ~/host/pixivdl.txt ${APPEND}