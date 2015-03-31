#!/bin/bash
# Put your Pixiv Username in by replacing $PIXIV_NAME
# The same for your password in $PIXIV_PASS
# Do not put a space between the keyword, the = sign, and your stuff.
PIXIV_NAME=$PIXIV_NAME PIXIV_PASS=$PIXIV_PASS python ~/host/git/puruselenium/pururinparser.py -m -t 1 -l -e ~/host/downloads -o ~/host/pixivdl.txt

### Additional Instructions
## Queuing up downloads
# Create a file in ~/host named pixivdl.txt
# You'll enter the user's work URL one per line.
# Example:
#(Their Profile Page)# http://www.pixiv.net/member.php?id=4164273
#(Their Works Page)  # http://www.pixiv.net/member_illust.php?id=2086403 
#(A Work Page)       # http://www.pixiv.net/member_illust.php?mode=medium&illust_id=49572009 

## Did your download fail in the middle of a big rip?
# Using the JUMP SYSTEM of download resuming using DL Links:
# Okay, if your download breaks or it for some reason quits early, here is how to fix it with 
# pixivdl.txt:
# In your pixivdl.txt say your download breaks on the 28th image (27 downloaded, but 28 didn't)
# Go to the work page of that failed download!
# Replace whatever link you had for the artist's user page before with that work's page.
# Now, append the text ">>28" after the URL (NO SPACE!)
# When you re-run, the first image will be that image, and it'll label it as #28. We resume where we
# it broke last time.

## Did a page just get stuck?
# Finally, Pixiv is a pretty heavy website. It needs to load TONS of stuff from all over. So
# if a page stops loading, you should just try selecting the address bar and hitting the return
# key. I should get it to start going again (maybe). WebDriver won't continue unless every dumb
# thing is loaded completely, and that includes slow ads, which is why AdblockPlus is packages in the repo.
# Most slowness is in the start of the execution (on the login and profile pages), but when it starts
# humming along it'll usually get through quite a lot between breakdowns.

