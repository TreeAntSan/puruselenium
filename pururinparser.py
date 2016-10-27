# Standard
from optparse import OptionParser
from time import sleep, time
from datetime import datetime
from string import capwords
from re import sub
from os.path import isfile, isdir, join, realpath, dirname
from os import mkdir, makedirs, walk, getenv
from shutil import rmtree
from imghdr import what
import sys
import zipfile
import pprint

# 3rd Party
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from requests import get

#### Intro
# This tool is in Python (written in 2.7.3) written in Summer 2014
# Updated to use Python 3 (3.5.2) in Fall 2016

# Use virtualenv for Python 3
# 0) Get Python 3 and use Linux (try an Ubuntu VM!) or MacOS.
# 1) Install virtualenv if you don't have it. https://virtualenv.pypa.io/en/stable/
# 2) Run `virtualenv -p python3 venv`
#    Note: To leave the virtual environment type `deactivate`
# 3) Run `source ./venv/bin/activate` ; you should see (venv) at the start of your terminal
# 4) Run `pip install -r requirements.txt`
# 5) Download geckodriver https://github.com/mozilla/geckodriver/releases and put it in your bin
# You can test to see if things work by running `python test.py`

# Example execution to a directory named ./downloads with a txt file of book urls ./downloads.txt
# python pururinparser.py -t 1 -c -e ./downloads -i ./downloads.txt

# The two libraries it uses is pypi Selenium, which can be found here:
#   https://pypi.python.org/pypi/selenium
# And Requests, which can be found here:
#   http://docs.python-requests.org/en/latest/index.html
# Using the tool pip can be very helpful:
#   https://pip.pypa.io/en/latest/installing.html

# Starting page can be either the first page OR the gallery page OR a gallery itself.
# Book name is determined by the name of the first page image.

# You can even import a txt file with the starting URL for each book you want.
# Just paste the full http:// link onto a single line by itself, nothing else.

# This will create zip/cbz files for you as an option. They are not compressed.

#### Docs
# General Selenium/Webdriver API reference for Python
#  http://selenium-python.readthedocs.org/en/latest/index.html


#### XPath+CSS+ID String Maintenance
# If things stop working. Get the plugin Firebug for Firefox, open it, navigate
# to a page, and use the Blue-Arrow-In-Box tool to investigate an element. Click it,
# then in list right click the hi-lited area and select "copy XPath".
# Replace the text in the variables below with that text (remember the single quotes!)
# Finding them http://selenium-python.readthedocs.org/en/latest/locating-elements.html

#Pururin
pururin_xpath_imageElement = '//a[@class="image-next"]/img'
pururin_xpath_nextPageButton = "//a[@class='square link-next image-next']"
pururin_xpath_galleryFirstPage = "//i[@class='fa fa-book']"
pururin_xpath_tableInfo = "//table[@class='table-info']"
pururin_xpath_tableInfo_sub = "/tbody/tr[{}]/td[{}]{}"
pururin_xpath_gallery = "//ul[@class='gallery-list']"
pururin_xpath_gallery_sub = "/li[{}]/div/a"
pururin_xpath_book_name = "//h1[@class='otitle']"
pururin_xpath_gallery_pages = "//div[@class='pager jumper']"
pururin_xpath_gallery_pages_sub = "/a[{}]"
pururin_xpath_gallery_pages_first = "/span"

#Pixiv
pixiv_css_user_name = "h1.user"
pixiv_xpath_first_image_item = "//li[@class='image-item '][{}]/a[2]"
pixiv_id_login_name = "login_pixiv_id"
pixiv_id_login_pass = "login_password"
pixiv_css_next_work = "li.after a"
pixiv_css_work_title_a = "div[class=ui-expander-target]>h1[class^=title]"
pixiv_css_work_title_b = "section[class=work-info]>h1[class^=title]"
pixiv_css_work_tab = "a.tab-works"
pixiv_css_tag_badge = "span.tag-badge"
pixiv_css_original_image = "img.original-image"
pixiv_css_original_image_close = "span.close.ui-modal-close"
pixiv_css_thumbnail_image = "div._layout-thumbnail.ui-modal-trigger"
pixiv_css_album_link = "div[class=works_display]>a"
pixiv_css_album_size = "span.total"
pixiv_css_album_big = "img"

#### Other globals
#Other
time_stamp_format = '%Y-%m-%d %H-%M-%S'
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0"
headers = {'User-Agent': user_agent}
current_directory = dirname(realpath(__file__))

#Retries
retries_allowed = 3
retry_refresh = True

#Cookies
driver_cookies = []
request_cookies = []
cookies_file_path = current_directory + '/cookies'

#AdBlockPlus
# Using a adblock plus v2.6.6.3876 load trick with custom adblock.xpi (with modified ui.js file)
# http://stackoverflow.com/q/20832159/3120546
# Pixiv otherwise takes FOREVER with terrible ads from Japanese servers that seldom load quickly
adblock_xpi = current_directory + '/adblock.xpi'
profile_location = current_directory + '/profilemodel'


# Grab an element that may not be there
def tryGrabbingElement(driver, elementType, elementAddress):
  try:
    if elementType == 'css':
      return driver.find_element_by_css_selector(elementAddress)
    if elementType == 'xpath':
      return driver.find_element_by_xpath(elementAddress)
    if elementType == 'id':
      return driver.find_element_by_id(elementAddress)
  except NoSuchElementException:
    return None


# Replace any potentially illegal characters with an underscore
# These usually come from tags.
def dirFileNameCleaner(dirfile, replacementChar = '_'):
  # return sub('[^\w\-_\. ]', '_', dirfile) # Aggresive
  return sub('[\\\/:\*?~"<>|]', replacementChar, dirfile) # Relaxed


# Downloads an image and names it from a URL.
def imageDownloader(url, directory, imageFileName="", cookie=None, referer=None):
  # Create the 'downloads' directory
  if not isdir(directory):
    makedirs(directory)

  # It assumes that the image file names are just numbers
  if len(imageFileName) == 0:
    # Parse the image name from the url
    imageFileName = url[url.rfind('/')+1:]
    imageFileName = fileNamePadder(imageFileName)

  # Download the image file
  if referer is not None:
    headers['referer'] = referer # Use referer to avoid 403 with Pixiv

  print("Getting this url now: {}".format(url))
  r = get(url, headers=headers, cookies=cookie)

  if r.status_code == 200:
    # Swap out file extension if the one we found was wrong
    detectedFileType = what('',h=r.content)
    if detectedFileType == 'jpeg': detectedFileType = 'jpg' # Use short jpg
    if detectedFileType not in imageFileName:
      imageFileName = "{}.{}".format(imageFileName[:imageFileName.rfind('.')], detectedFileType)
      print("Detected the wrong filename, swapped to {}".format(detectedFileType))

    with open("{}/{}".format(directory, imageFileName), 'wb') as imageFile:
      imageFile.write(r.content)
  else:
    print("Problem! Status {}: {}".format(r.status_code, url))


# Improves the filename by giving a padded number.
# CDisplay for Windows, for example, fails at ordering without them. (1, 11, 12,..., 19, 2, 20,...)
# Limits file names before number and extension to 50 characters
def fileNamePadder(fileName):
  return fileName[:fileName.rfind('-')+1][:50] + fileName[fileName.rfind('-')+1:fileName.rfind('.')].zfill(3) + fileName[fileName.rfind('.'):]


# Function archives the contents of the desired directory. Only writes to an existing zip object.
def createArchive(directory, zip):
  for root, dirs, files, in walk(directory):
    for file in files:
      zip.write(join(root, file))


# Parses the contents of the table-info element for tags.
# Keep in mind that if there is more than one artist, for example, it'll say 'Artists'
# So instead of exact matches I use find. So if perhaps there is more than one
# parody, expect a possible use of 'parodies', so search for 'parod'
def tagListGrabber(desiredTagName, driver):
  for x in range(1,20): # Try up to 19 elements
    try:
      xpath_tagCheck = pururin_xpath_tableInfo + pururin_xpath_tableInfo_sub
      tagElement = driver.find_element_by_xpath(xpath_tagCheck.format(x, '1', ''))
      if tagElement.text.lower().find(desiredTagName.lower()) != -1:
        tagValueElement = driver.find_element_by_xpath(xpath_tagCheck.format(x, '2', '/ul/li/a'))
        return dirFileNameCleaner(tagValueElement.text) # Remove any illegal characters
    except NoSuchElementException:
      if (x == 1):
        break # If this broke on the first time, then just give up - wrong page.
      pass # Do nothing, we coo.

  return '' # Didn't get the tag.


# Get the book's name
def bookNameGrabber(driver):
  try:
    bookNameElement = driver.find_element_by_xpath(pururin_xpath_book_name)
    bookName = bookNameElement.text.split(' / ')[0] # Split on / (Japanese name)

    bookNameSplit = bookName.split(' | ') # Split on Romanji title | English translation
    if len(bookNameSplit) == 2:
      return bookNameSplit[1]
    else:
      return bookName
  except NoSuchElementException:
    return "ERROR_BLANK_BOOK_NAME"


# If you give a gallery page in the url, this will parse all the books on the gallery page
# and spit them all back out in a simple list.
# If it didn't work, returns an empty list!
def galleryGrab(driver):

  newLinks = []
  extraPages = 0

  # Grab gallery page links (galleries with multiple pages)
  try:
    driver.find_element_by_xpath(pururin_xpath_gallery_pages)

    # Only grab page links from the first page. This was a crappy way to detect it.
    firstPage = driver.find_element_by_xpath(pururin_xpath_gallery_pages + pururin_xpath_gallery_pages_first)

    # Only grab the first 10 links (2 -> 11) at max.
    if firstPage.text == '1':
      for x in range(1, 11):
        try:
          xpath_pageCheck = pururin_xpath_gallery_pages + pururin_xpath_gallery_pages_sub
          pageElement = driver.find_element_by_xpath(xpath_pageCheck.format(x))
          newLink = pageElement.get_attribute('href') # Grab the new page url
          newLinks.append(newLink) # Add it to the list
          extraPages += 1
        except NoSuchElementException:
          if extraPages > 0:
            print("Found {} more pages for that gallery, they'll be dl'd eventually!".format(extraPages))
          break # Stop, we've hit the end


  except NoSuchElementException:
    pass # Continue...

  # Grab new comics
  try:
    driver.find_element_by_xpath(pururin_xpath_gallery)
  except NoSuchElementException:
    return [] # Got nothing

  for x in range(1, int(options.gallery)+1): # Try elements 1->n gallery arg
    try:
      xpath_bookCheck = pururin_xpath_gallery + pururin_xpath_gallery_sub
      bookElement = driver.find_element_by_xpath(xpath_bookCheck.format(x))
      newLink = bookElement.get_attribute('href') # Grab the book url
      newLinks.append(newLink)  # Add it to the list
    except NoSuchElementException:
      break # Stop, we've hit the end

  return newLinks # Return the booty!


# All the pururin-side magic
def pururin(driver, startURL, urlList, outputDir, bookNumber):
  # Go to the starting page!
  driver.get(startURL)

  # Handle gallery pages
  galleryLinks = galleryGrab(driver)
  if len(galleryLinks) > 0:
    print("That last link was a gallery! {} books were found:".format(len(galleryLinks)))

    # Some fuckin' fancy footwork here. In-place alter to print out book titles from html links
    print(capwords(', '.join([bookUrl[bookUrl.rfind('/')+1:bookUrl.rfind('.html')] for bookUrl in galleryLinks]).replace('-', ' ')))

    # Insert the new books after the gallery link (must keep it to keep place)
    # (Book number starts at 1, not 0)
    urlList[bookNumber:bookNumber] = galleryLinks

    # Start the loop over again, but this time with an updated urlList
    return ["!@#$CONTINUE!@#$",""]

  # Attempt to grab the artist name if we're on the correct gallery page.
  artistName = tagListGrabber('artist', driver)
  artistName = artistName.split(',')[0] # Sometimes aliases are used. Grab just the first one.

  # Attempt to grab a parody tag.
  parodyTagList = tagListGrabber('parod', driver)
  parodyTag = ""
  for parody in parodyTagList.split(','):
    if parody.lower() != 'original':
      # Grab the first parody tag that isn't 'Original'.
      parodyTag = parody.strip() # Strip surrounding white space

  # Get book name
  bookName = bookNameGrabber(driver)

  # Add first parody to front if available (start from Gallery Page)
  if len(parodyTag) > 0:
    bookName = "{} - {}".format(parodyTag, bookName)

  # Add the artist name to front if available (start from Gallery Page)
  if len(artistName) > 0:
    bookName = "{} - {}".format(artistName, bookName)

  # Print out title to console
  print("Title: {}".format(bookName))

  # Check for bad name and report it if found
  cleanBookName = dirFileNameCleaner(bookName, '-')
  if cleanBookName != bookName:
    print("Renamed title: {}".format(cleanBookName))
    bookName = cleanBookName

  # Navigate to to the first page if we're on a gallery or thumbnails page.
  try:
    galleryFirstPage = driver.find_element_by_xpath(pururin_xpath_galleryFirstPage)
    galleryFirstPage.click()
  except NoSuchElementException:
    pass # Do nothing, we coo.


  pageLimit = int(options.pageLimit)

  urlString = ""
  pastImageUrl = "" # Prevent situations where it'll infinitely redownload one page.

  for page in range(pageLimit):

    imageUrl = ""

    # Deal with the image element
    try:
      imageElement = driver.find_element_by_xpath(pururin_xpath_imageElement)
      imageUrl = imageElement.get_attribute('src')

      if imageUrl != pastImageUrl:
        urlString += "{}\n".format(imageUrl)
        pastImageUrl = imageUrl
        # Download imageUrl
        if options.download or options.zip or options.cbz:
          imageDownloader(imageUrl, "{}/{}".format(outputDir, bookName), "", None, driver.current_url)

      # Throttle the speed, otherwise Selenium will rip through pages a half-second a piece.
      sleep(int(options.throttle))

      # Click the next button.
      nextPageButton = driver.find_element_by_xpath(pururin_xpath_nextPageButton)
      nextPageButton.click()

    except NoSuchElementException:
      print("Reached end for \"{}\", got through {} pages.".format(bookName, page))
      break

  print("Done with {}".format(bookName))
  return [bookName, urlString]


# Pixiv album parser, returns array of image URLs
def pixivAlbumGrab(driver, albumURL):
  albumURL = albumURL.replace('manga', 'manga_big') + '&page='  # Get the full page link
  albumSize = int(driver.find_element_by_css_selector(pixiv_css_album_size).text)
  print("Grabbing URLs: There should be {} images in this album...".format(albumSize))

  itemUrlPairs = []
  albumExhausted = False
  for albumItemNumber in range(albumSize):
    albumImageLargeURL = albumURL + str(albumItemNumber)
    driver.get(albumImageLargeURL)

    itemUrlPairs.append([albumImageLargeURL, driver.find_element_by_css_selector(pixiv_css_album_big).get_attribute('src')])
  return itemUrlPairs # Return the links!


# Jump is the jump in the grand-count of this user's works. If a user has 200 works, then it'll be 1-200.
#   If you want to start counting again from a certain number (such as 201) write >>201
# First is the first link on a work's overview page. If you want to resume your DL on the 9th image
#   viewable on the page, then set <<9
# Limit is the limit of works you wanna download. Say you return to a user after downloading 20 works.
#   They just released two new works, and you want those two new ones. Well, write >>21||2 and it'll
#   download the first two items and make them #21 and #22 and stop there.
def pixivDownloadConfig(url):
  jumpPos = url.rfind('>>') if url.rfind('>>') != -1 else None
  firstPos = url.rfind('<<') if url.rfind('<<') != -1 else None
  limitPos = url.rfind('||') if url.rfind('||') != -1 else None
  global redownload_jump
  global redownload_first
  global redownload_limit
  redownload_jump = int(url[jumpPos+2:firstPos or limitPos]) if jumpPos > 0 else 1 # Default to 1
  redownload_first = int(url[firstPos+2:limitPos]) if firstPos > 0 else 1 # Default to 1
  redownload_limit = int(url[limitPos+2:]) if limitPos > 0 else 0 # Default to 1

  strip = None
  if jumpPos is not None:
    strip = jumpPos
  elif firstPos is not None:
    strip = firstPos
  elif limitPos is not None:
    strip = limitPos

  return url[:strip]

# All the pixiv-side magic
def pixiv(driver, startURL, loginNeeded, outputDir):
  startURL = pixivDownloadConfig(startURL) # Detect re-download information
  if redownload_jump != 1:
    print("->Jump count @{}".format(redownload_jump))
  if redownload_first != 1:
    print("->First work @{}".format(redownload_first))
  if redownload_limit != 0:
    print("->Limit work @{}".format(redownload_limit))

  # Go to the starting page!
  driver.set_page_load_timeout(15)
  try:
    driver.get(startURL)
  except TimeoutException:
    driver.refresh()

  # Wait, do we need to log in first?
  if loginNeeded:
    tryPixivCookies(driver)
    pixivLogin(driver)

  # On their profile or something, hit their "Works" tab link
  if "member_illust" not in driver.current_url:
    try:
      driver.find_element_by_css_selector(pixiv_css_work_tab).click()
    except TimeoutException:
      driver.refresh()

  # Let's create a name for this book
  userNameElement = tryGrabbingElement(driver, 'css', pixiv_css_user_name)
  if userNameElement is not None:
    userName = userNameElement.text
  else:
    userName = "UnknownUser"
    if not options.time:
      options.time = True # Force the timestamp option

  tagElement = tryGrabbingElement(driver, 'css', pixiv_css_tag_badge)
  if tagElement is not None:
    tag = " - " + tagElement.text
  else:
    tag = ""

  # Book's title is "user's name - tag"
  bookName = userName + tag
  bookName = dirFileNameCleaner(bookName, '-')

  print("Book title: {}".format(bookName))

  # Alrighty, time to get some images!
  if "illust_id" not in driver.current_url:
    # We're on their works main page, let's click their first work...
    try:
      driver.find_element_by_xpath(pixiv_xpath_first_image_item.format(redownload_first)).click()
    except TimeoutException:
      driver.refresh()

  # ------ We're now viewing works ------ Loop time! ------
  workNumber = redownload_jump - 1 # Default this equals 0, use --jump and we start at a new number
  exhausted = False
  while not exhausted:
    workURL = None
    mightBeLastPage = True
    workNumber += 1
    urlString = ""

    if redownload_limit != 0:
      if workNumber > redownload_limit + (redownload_jump - 1):
        print("We reached the end of a limited job of {} works.".format(redownload_limit))
        break # Breaks the 'exhausted' loop, effectively going straight to this function's return.

    # Let's grab a work title
    workTitleElement = tryGrabbingElement(driver, 'css', pixiv_css_work_title_a)
    if workTitleElement is None:
      workTitleElement = tryGrabbingElement(driver, 'css', pixiv_css_work_title_b)

    if workTitleElement is not None:
      workTitle = workTitleElement.text[:25] # Limit the name to 25 characters
    else:
      workTitle = "image"

    # Let's pretend to be a real human and click the full view option
    thumbNailElement = tryGrabbingElement(driver, 'css', pixiv_css_thumbnail_image)
    if thumbNailElement is not None:
      thumbNailElement.click()

      # Grab original image element. If not there, then it's an album (probably)
      originalImageElement = tryGrabbingElement(driver, 'css', pixiv_css_original_image)
      if originalImageElement is not None:
        imageUrl = originalImageElement.get_attribute('src')
        urlString += imageUrl + "\n"

        # Grab the file extension
        argumentQM = imageUrl.rfind('?')
        argumentQM = None if argumentQM < 0 else argumentQM
        fileExtension = imageUrl[imageUrl.rfind('.'):argumentQM]

        # Let's give this work a nice, long name
        imageName = "{} - {} - {}{}".format(bookName, str(workNumber).zfill(3), workTitle, fileExtension)
        imageName = dirFileNameCleaner(imageName)

        # Let's download it!
        print("Attempting DL: {}...".format(imageName))
        imageDownloader(imageUrl, "{}/{}".format(outputDir, bookName), imageName, request_cookies, driver.current_url)

        # Click it closed
        driver.find_element_by_css_selector(pixiv_css_original_image_close).click()
      else:
        print("Was on a normal work page but I couldn't find \"{}\"".format(pixiv_css_original_image))

    # ------- ALBUM ------- ALBUM ------- ALBUM ------- ALBUM ------- ALBUM -------
    else:
      albumThumbNailElement = tryGrabbingElement(driver, 'css', pixiv_css_album_link)
      if albumThumbNailElement is not None: # We're in an album!

        # Nagivate directly to album URL (clicking opens a new window, bad for WebDriver)
        workURL = driver.current_url
        albumURL = albumThumbNailElement.get_attribute('href')
        try:
          driver.get(albumURL)
        except TimeoutException:
          driver.refresh()

        # Grab all the image URLs
        print("Grabbing URLs: {} - {} - {}... ".format(bookName, str(workNumber).zfill(3), workTitle))
        albumImages = pixivAlbumGrab(driver, albumURL)
        # albumImages is a list of lists with [referrer url, image url]

        albumSeriesNumber = 1
        for imageUrlPair in albumImages:
          urlString += imageUrlPair[1] + "\n"

          # Grab the file extension
          argumentQM = imageUrlPair[1].rfind('?')
          argumentQM = None if argumentQM < 0 else argumentQM
          fileExtension = imageUrlPair[1][imageUrlPair[1].rfind('.'):argumentQM]

          # Let's give this work a nice, long name
          imageName = "{} - {} - {}_{}{}".format(bookName, str(workNumber).zfill(3), workTitle, str(albumSeriesNumber).zfill(3), fileExtension)
          imageName = dirFileNameCleaner(imageName)

          # Let's download it!
          print("Attempting DL: {}...".format(imageName))
          imageDownloader(imageUrlPair[1], "{}/{}".format(outputDir, bookName), imageName, request_cookies, imageUrlPair[0])
          albumSeriesNumber += 1 # Doing a series, add a new number

        try:
          driver.get(workURL) # Return to the work detail page
        except TimeoutException:
          driver.refresh()
      else:
        print("Wasn't an illustration or album! Maybe an animation?")

    # Move onto the next element
    retriesLeft = retries_allowed # Grab global setting of allowed retries

    while retriesLeft+1 != 0 and mightBeLastPage:
      nextWorkElement = tryGrabbingElement(driver, 'css', pixiv_css_next_work)

      if nextWorkElement is not None: # Success :)
        try:
          nextWorkElement.click()
          mightBeLastPage = False
        except TimeoutException:
          # Thought it might be ready, but didn't work!
          print("Retrying to find the next work button. {} retries left...".format(retriesLeft))
          retriesLeft -= 1 # One retry taken!

          if retry_refresh: # If we're serious, we can try refreshing...
            if workURL is not None:
              print("Trying returning to workURL {}".format(workURL))
              driver.get(workURL) # Album failure, more effective to re-get workURL
            else:
              print("Trying refresh of current page {}".format(driver.current_url))
              driver.refresh()

      else:                           # Failed :(
        # Wasn't there, didn't work.
        print("Retrying to find the next work button. {} retries left...".format(retriesLeft))
        retriesLeft -= 1 # One retry taken!
        if retry_refresh: # If we're serious, we can try refreshing...
          driver.refresh()

    if mightBeLastPage:
      # Retries exhausted, maybe we really have hit the end of the book...
      exhaustion = True

  print("Reached the end of Pixiv Book: \"{}\"".format(bookName))
  return [bookName, urlString]


# -------- COOKIES?!?!??! --------
#http://stackoverflow.com/questions/7854077/using-a-session-cookie-from-selenium-in-urllib2
def getDriverCookies(driver): # Load driver_cookies from driver
  driver_cookies = driver.get_cookies()
  print("Got cookies, cookie size = {}.".format(str(len(driver_cookies))))
  # print(pp.pprint(driver_cookies))


def addRequestCookies():  # Load request_cookies into driver_cookies
  for cookie in driver_cookies:
    request_cookies[cookie["name"]]=cookie["value"]

  print("Loaded request cookies.")


def addDriverCookies(driver): # Load driver_cookies into driver
  for cookie in driver_cookies:
    driver.add_cookie(cookie)


def loadCookiesFile(filePath):  # Load cookies file into driver_cookies
  if isfile(filePath):
    print("Reading driver cookies from {}.".format(filePath))
    with open(filePath, 'r') as inFile:
      driver_cookies = eval(inFile.read())

    if len(driver_cookies) < 1:
      print("File found, but nothing in {}.".format(filePath))
      return False # Got something, but it's empty

    return True
  else:
    print ("Didn't find driver cookies in {}.".format(filePath))
    return False


def saveCookiesFile(filePath):  # Write driver_cookies to file
  print("Writing driver cookies to file.")
  with open(filePath, 'w') as inFile:
    inFile.write(str(driver_cookies))


def tryPixivCookies(driver):  # Attempt to load cookies from file
  if loadCookiesFile(cookies_file_path):
    addDriverCookies(driver) # Write driver_cookies to our driver
    addRequestCookies() # Write driver_cookies to request_cookies
    return True # We loaded something, maybe we're logged in?
  else:
    return False # We loaded nothing, no way we're logged in.


# Since Pixiv's good stuff is being a login you need to log in first!
def pixivLogin(driver):

  if tryGrabbingElement(driver, 'id', pixiv_id_login_name) is not None: # We're not logged in
    userName = getenv("PIXIV_NAME")
    passWord = getenv("PIXIV_PASS")

    if len(userName) == 0 or len(passWord) == 0:
      print("Hey, you need to define your Pixiv login info into the two env vars:")
      print("$PIXIV_NAME and $PIXIV_PASS. Edit the pixiv.sh file in a text editor!")
      quit()

    driver.find_element_by_id(pixiv_id_login_name).send_keys(userName)
    driver.find_element_by_id(pixiv_id_login_pass).send_keys(passWord, Keys.RETURN)

    print("Logging in to Pixiv with {}".format((userName)))
    sleep(3)

    # We're now logged in, let's save it.
    getDriverCookies(driver) # Save driver cookies to driver_cookies
    addRequestCookies() # Convert driver_cookies to request_cookies
    saveCookiesFile(cookies_file_path) # Write new driver_cookies to file for next run


# The main function. Starts with a string array of starting URLs.
def imageURLCrawler(urlList):
  # Start up Firefox
  print("Adblock xpi: {}\nAdblock profile: {}".format(adblock_xpi, profile_location))
  firefoxProfile = webdriver.FirefoxProfile(profile_location)
  firefoxProfile.add_extension(adblock_xpi)

  # Pixiv slow loading http://stackoverflow.com/a/22406998/3120546 fix??
  firefoxProfile.set_preference("webdriver.load.strategy", "unstable");

  driver = webdriver.Firefox(firefox_profile=firefoxProfile)
  driver.implicitly_wait(10) # ?? Tries anyway if the page keeps loading after 5 sec?

  outputDir = options.export
  if len(outputDir) == 0:
    print("WARNING: CANNOT HAVE A BLANK OUTPUT DIRECTORY. QUITTING.")
    quit()

  # Print out some stuff.
  print("\n-------\nStarting image crawler...")
  if len(options.startURL) > 0:
    print("Starting URL: {}".format(options.startURL))
  if len(options.inputList) > 0:
    print("Opening list file {}".format(options.inputList))
  if options.writeFile:
    print("Writing image urls to file. View saved files in {}".format(outputDir))
  if options.download:
    print("Downloading images enabled. View saved files in {}".format(outputDir))
  if options.cbz:
    print("Downloading and archiving images enabled. View saved .cbz in {}".format(outputDir))
  elif options.zip:
    print("Downloading and archiving images enabled. View saved .zip in {}".format(outputDir))
  print("Set to download {} book(s)".format(len(urlList)))
  print("Throttle set to {} second(s).".format(options.throttle))

  pixivLoginNeeded = True
  bookNumber = 0
  bookName = ""
  # Book loop. If there are multiple books loaded, it'll do each one in this loop.
  for startURL in urlList:
    bookNumber += 1

    if startURL[0] == '#':
      continue # Comment, skip!
    if startURL == 'stop':
      print("Stopping early due to 'stop' line!")
      break # Stop what we're doing
    if len(startURL) == 0:
      continue # Skip blank lines
    if 'http' not in startURL and 'html' not in startURL:
      print("Hey, this URL looks broken")
      continue # No http nor html? Maybe a jpg, maybe junk!

    print("-------\nViewing link {} of {}: {}".format(bookNumber, len(urlList), startURL))

    # A Pururin Link!
    if 'pururin' in startURL:
      returned = pururin(driver, startURL, urlList, outputDir, bookNumber)
      bookName = returned[0]
      urlString = returned[1]

    # A Pixiv Link!
    elif 'pixiv' in startURL:
      bookName = pixiv(driver, startURL, pixivLoginNeeded, outputDir)[0]
      pixivLoginNeeded = False;

    else:
      print("I don't think this link will work: {}".format(startURL))
      continue # Link isn't recognized, just move onto the next

    if bookName == "!@#$CONTINUE!@#$":
      # Using a dumb string because I moved code from this function into pururin() way later.
      continue # Gallery, restart the loop.


    ### End of loop for this gallery
    # Write the archive file.
    if options.zip or options.cbz:
      if len(bookName) == 0:
        print("WARNING. BOOKNAME IS BLANK. CANNOT ARCHIVE {}/. QUITTING.".format(outputDir))
        quit()
      else:

        extension = 'zip' if options.zip else 'cbz'

        zipf = zipfile.ZipFile("{}/{}.{}".format(outputDir, bookName, extension), 'w')
        createArchive("{}/{}".format(outputDir, bookName), zipf)
        zipf.close()

        print("Wrote archive \"{}/{}.{}\"".format(outputDir, bookName, extension))

        # If the download option isn't set, delete the download directory.
        if not options.download:
          try:
            rmtree("{}/{}".format(outputDir, bookName))
          except OSError as e:
            print("Crap, something broke when trying to delete but we'll continue on...")


        else:
          print("Wrote to directory \"{}/{}/\"".format(outputDir, bookName))

    # Write the output file.
    if options.writeFile and len(bookName) > 0:
      if not isdir(outputDir):
        mkdir(outputDir)

      with open("{}/{}.txt".format(outputDir,bookName), 'w') as outfile:
        outfile.write(urlString)
        print("Wrote to file \"{}/{}.txt\"".format(outputDir, bookName))

    # Write log file of successful downloads
    if options.dls:
      if not isdir(outputDir):
        mkdir(outputDir)

      with open("{}/{}".format(outputDir, options.dls), 'a') as successFile:
        successFile.write("\n{}".format(startURL))
        print("Wrote successful dl to file \"{}/{}\"".format(outputDir, options.dls))

    # Sleep a little bit (at least one second)
    sleep(1 + int(options.throttle))


  ### End of urlList for loop
  driver.quit()


#### Parser Stuff
parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL", default='', metavar="startURL")
parser.add_option("-i", "--inputList", help="List file (\\n delimit)", default='', metavar="filename")
parser.add_option("-d", "--dls", help="Output Successful DLs", default='successdls.txt', metavar="filename")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
parser.add_option("-g", "--gallery", help="Gallery page size", default='20', metavar="integer")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")
parser.add_option("-e", "--export", help="Export directory", default='output', metavar="string")
parser.add_option("-w", "--writeFile", help="Write URLs to file", default=False, action="store_true")
parser.add_option("-l", "--download", help="Download images to directory", default=False, action="store_true")
parser.add_option("-z", "--zip", help="Create a zip file ...", default=False, action="store_true")
parser.add_option("-c", "--cbz", help="OR: Create a cbz file", default=False, action="store_true")

(options, args) = parser.parse_args()

urlList = []

# Open the list file (if one was specified)
if isfile(options.inputList):
  with open(options.inputList, 'r') as listFile:
    listContents = listFile.read()
  urlList = listContents.split("\n")

# Append the startURL to the urlList
if len(options.startURL) > 0:
  urlList.append(options.startURL)

# Do it!
returnArray = imageURLCrawler(urlList)
print("-------\nDone!")
