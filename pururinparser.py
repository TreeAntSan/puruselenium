# Standard
from optparse import OptionParser
from time import sleep, time
from datetime import datetime
from string import split, capwords, replace, find, lower, strip
from re import sub
from os.path import isfile, isdir, join, realpath, dirname
from os import mkdir, makedirs, walk, getenv
from shutil import rmtree
import sys
import zipfile
import pprint
pp = pprint.PrettyPrinter(indent=2)
# use "pp.pprint(stuff)" to pprint your stuff

# 3rd Party
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from requests import get

#### Intro
# This tool is in Python (written in 2.7.3) written in Summer 2014

# The two libraries it uses is pypi Selenium, which can be found here:
# 	https://pypi.python.org/pypi/selenium
# And Requests, which can be found here:
# 	http://docs.python-requests.org/en/latest/index.html
# Using the tool pip can be very helpful:
# 	https://pip.pypa.io/en/latest/installing.html

# Download Python 2.7.X (whatever is current X), figure out how to get
# command line access, navigate your terminal to the location
# of this program, run "python pururinparser.py --help"

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
pururin_xpath_doubleButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[4]/a[2]' # WESTERN ORDER!!!
pururin_xpath_imageElementA = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[1]'
pururin_xpath_imageElementB = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[2]'
pururin_xpath_nextPageButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[1]/a[2]'
pururin_xpath_galleryFirstPage = "//ul[@class='thumblist']/li[1]/a/img[1]"
pururin_xpath_tableInfo = "//table[@class='table-info']"
pururin_xpath_gallery = "//ul[@class='gallery-list']"

#Pixiv
pixiv_css_user_name = "h1.user"
pixiv_xpath_first_image_item = "//li[@class='image-item '][%s]/a[2]"
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
def directoryCleaner(directory):
	# return sub('[^\w\-_\. ]', '_', directory) # Aggresive
	return sub('[\\\/:\*?"<>|]', '_', directory) # Relaxed


# Downloads an image and names it from a URL.
def imageDownloader(url, directory, imageFileName="", cookie=None, referer=None):
	# Create the 'downloads' directory
	if not isdir(directory):
		makedirs(directory)

	if len(imageFileName) == 0:
		# Parse the image name from the url
		imageFileName = url[url.rfind('/')+1:]
		imageFileName = fileNamePadder(imageFileName)

	# Download the image file
	if referer is not None:
		headers['referer'] = referer # Use referer to avoid 403 with Pixiv

	print "Getting this url now: %s" % url
	r = get(url, headers=headers, cookies=cookie)

	# Write the image file
	imageFile = open(directory + '/' + imageFileName, 'w')
	imageFile.write(r.content)
	imageFile.close()


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
			xpath_tagCheck = pururin_xpath_tableInfo + '/tbody/tr[%s]/td[%s]%s'
			tagElement = driver.find_element_by_xpath(xpath_tagCheck % (x, '1', ''))
			if find(lower(tagElement.text), lower(desiredTagName)) != -1:
				tagValueElement = driver.find_element_by_xpath(xpath_tagCheck % (x, '2', '/ul/li/a'))
				return directoryCleaner(tagValueElement.text) # Remove any illegal characters
		except NoSuchElementException:
			if (x == 1):
				break # If this broke on the first time, then just give up - wrong page.
			pass # Do nothing, we coo.

	return '' # Didn't get the tag.


# If you give a gallery page in the url, this will parse all the books on the gallery page
# and spit them all back out in a simple list.
# If it didn't work, returns an empty list!
def galleryGrab(driver):
	try:
		galleryElement = driver.find_element_by_xpath(pururin_xpath_gallery)
	except NoSuchElementException:
		return [] # Got nothing

	newLinks = [] # If this is a gallery, we'll store the urls of each one!
	for x in range(1, int(options.gallery)+1): # Try elements 1->n gallery arg
		try:
			xpath_bookCheck = pururin_xpath_gallery + '/li[%s]/div/a'
			bookElement = driver.find_element_by_xpath(xpath_bookCheck % x)
			newLink = bookElement.get_attribute('href') # Grab the book url
			newLinks.append(newLink)	# Add it to the list
		except NoSuchElementException:
			break # Stop, we've hit the end

	return newLinks	# Return the booty!


# All the pururin-side magic
def pururin(driver, startURL, urlList, outputDir, bookNumber):
	# Go to the starting page!
	driver.get(startURL)

	# Handle gallery pages
	galleryLinks = galleryGrab(driver)
	if len(galleryLinks) > 0:
		print "That last link was a gallery! %s books were found:" % len(galleryLinks)

		# Some fuckin' fancy footwork here. In-place alter to print out book titles from html links
		print capwords(replace(', '.join([bookUrl[bookUrl.rfind('/')+1:bookUrl.rfind('.html')] for bookUrl in galleryLinks]), '-', ' '))

		# Insert the new books after the gallery link (must keep it to keep place)
		urlList[bookNumber:bookNumber] = galleryLinks

		# Start the loop over again, but this time with an updated urlList
		return ["!@#$CONTINUE!@#$",""]

	# Attempt to grab the artist name if we're on the correct gallery page.
	artistName = tagListGrabber('artist', driver)
	artistName = split(artistName, ',')[0] # Sometimes aliases are used. Grab just the first one.

	# Attempt to grab a parody tag.
	parodyTagList = tagListGrabber('parod', driver)
	parodyTag = ""
	for parody in split(parodyTagList, ','):
		if lower(parody) != 'original':
			# Grab the first parody tag that isn't 'Original'.
			parodyTag = parody.strip() # Strip surrounding white space

	# Navigate to to the first page if we're on a gallery or thumbnails page.
	try:
		galleryFirstPage = driver.find_element_by_xpath(pururin_xpath_galleryFirstPage)
		galleryFirstPage.click()
	except NoSuchElementException:
		pass # Do nothing, we coo.

	pagesPer = 1
	if options.dual:	# Switch to 'western' dual page mode
		for x in range(10):	# Sometimes this loads in slow, so we try 10 times with 1 sec rests
			try:
				doubleButton = driver.find_element_by_xpath(pururin_xpath_doubleButton)
				doubleButton.click()
				pagesPer = 2
				break	# It worked! Break from the loop.
			except NoSuchElementException:
				sleep(1) # It didn't work! Rest for a second

	pageLimit = int(options.pageLimit)

	urlString = ""
	bookName = "ERROR_BLANK_BOOK_NAME" # Need to write something
	pastImageUrlA = "" # Prevent situations where it'll infinitely redownload one page.
	pastImageUrlB = "" # Work around for uneven pages in dual mode.

	for page in range(pageLimit):

		imageUrlA = ""
		imageUrlB = ""

		# Deal with the image element
		try:
			imageElementA = driver.find_element_by_xpath(pururin_xpath_imageElementA)
			imageUrlA = imageElementA.get_attribute('src')

			if imageUrlA != pastImageUrlA and imageUrlA != pastImageUrlB:
				urlString += imageUrlA + "\n"
				pastImageUrlA = imageUrlA

				# Name the book from the last '/'+1 to the last '-'
				if bookName == "ERROR_BLANK_BOOK_NAME":
					bookName = imageUrlA[imageUrlA.rfind('/')+1:imageUrlA.rfind('-')]

					# Format it nice. 'book-title-thing' becomes 'Book Title Thing'
					bookName = capwords(replace(bookName, '-', ' '))

					# Add first parody to front if available (start from Gallery Page)
					if len(parodyTag) > 0:
						bookName = parodyTag + ' - ' + bookName

					# Add the artist name to front if available (start from Gallery Page)
					if len(artistName) > 0:
						bookName = artistName + ' - ' + bookName

					# Print out title to console
					print "Title: %s" % bookName

				# Download imageUrlA
				if options.download or options.zip or options.cbz:
					imageDownloader(imageUrlA, outputDir + '/' + bookName, "", None, driver.current_url)

				print imageUrlA

		except NoSuchElementException:
			print "Reached end for \"%s\" on A, got through around %s pages." % (bookName, pagesPer*page)
			break


		# Deal with a second image element if in dual mode
		if options.dual:
			try:
				imageElementB = driver.find_element_by_xpath(pururin_xpath_imageElementB)
				imageUrlB = imageElementB.get_attribute('src')

				# When there is just one image imageUrlB will repeat itself.
				# One page could appear if there is a double-wide page or there is only one page left.
				if imageUrlB != pastImageUrlB and imageUrlB != imageUrlA and imageUrlB != pastImageUrlA:

					# When there are double-wide images, the site automatically shows only one image.
					# It fails in a special way with imageUrlB == None, so if I see this, we'll side step
					# the need to grab imageUrlB this time.
					if imageUrlB is not None:
						urlString += imageUrlB + "\n"
						pastImageUrlB = imageUrlB

						# Download imageUrlB
						if options.download or options.zip or options.cbz:
							imageDownloader(imageUrlB, outputDir + '/' + bookName, "", None, driver.current_url)

						print imageUrlB
					else:
						page -= 1
			except NoSuchElementException:
				pass # Do nothing, we coo.


		# Throttle the speed, otherwise Selenium will rip through pages a half-second a piece.
		sleep(int(options.throttle))

		# Click the next button.
		nextPageButton = driver.find_element_by_xpath(pururin_xpath_nextPageButton)
		nextPageButton.click()

	print "Done with %s" % bookName
	return [bookName, urlString]


# Pixiv album parser, returns array of image URLs
def pixivAlbumGrab(driver, albumURL):
	albumURL = albumURL.replace('manga', 'manga_big') + '&page='	# Get the full page link
 	albumSize = int(driver.find_element_by_css_selector(pixiv_css_album_size).text)
 	print "Grabbing URLs: There should be %s images in this album..." % albumSize

	itemUrlPairs = []
	albumExhausted = False
	for albumItemNumber in range(albumSize):
		albumImageLargeURL = albumURL + str(albumItemNumber)
		driver.get(albumImageLargeURL)

		itemUrlPairs.append([albumImageLargeURL, driver.find_element_by_css_selector(pixiv_css_album_big).get_attribute('src')])
	return itemUrlPairs # Return the links!


# Jump is the jump in the grand-count of this user's works. If a user has 200 works, then it'll be 1-200.
#		If you want to start counting again from a certain number (such as 201) write >>201
# First is the first link on a work's overview page. If you want to resume your DL on the 9th image
# 	viewable on the page, then set <<9
# Limit is the limit of works you wanna download. Say you return to a user after downloading 20 works.
#		They just released two new works, and you want those two new ones. Well, write >>21||2 and it'll
#		download the first two items and make them #21 and #22 and stop there.
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
		print "->Jump count @%s" % redownload_jump
	if redownload_first != 1:
		print "->First work @%s" % redownload_first
	if redownload_limit != 0:
		print "->Limit work @%s" % redownload_limit

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
	bookName = directoryCleaner(bookName)

	print u"Book title: %s" % bookName

	# Alrighty, time to get some images!
	if "illust_id" not in driver.current_url:
		# We're on their works main page, let's click their first work...
		try:
			driver.find_element_by_xpath(pixiv_xpath_first_image_item % redownload_first).click()
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
				print "We reached the end of a limited job of %s works." % redownload_limit
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
				imageName = u"{} - {} - {}{}".format(bookName, str(workNumber).zfill(3), workTitle, fileExtension)
				imageName = directoryCleaner(imageName)

				# Let's download it!
				print "Attempting DL: %s..." % imageName
				imageDownloader(imageUrl, outputDir + '/' + bookName, imageName, request_cookies, driver.current_url)

				# Click it closed
				driver.find_element_by_css_selector(pixiv_css_original_image_close).click()
			else:
				print "Was on a normal work page but I couldn't find \"%s\"" % pixiv_css_original_image

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
				print "Grabbing URLs: %s... " % (u"{} - {} - {}".format(bookName, str(workNumber).zfill(3), workTitle))
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
					imageName = u"{} - {} - {}_{}{}".format(bookName, str(workNumber).zfill(3), workTitle, str(albumSeriesNumber).zfill(3), fileExtension)
					imageName = directoryCleaner(imageName)

					# Let's download it!
					print "Attempting DL: %s..." % imageName
					imageDownloader(imageUrlPair[1], outputDir + '/' + bookName, imageName, request_cookies, imageUrlPair[0])
					albumSeriesNumber += 1 # Doing a series, add a new number

				try:
					driver.get(workURL) # Return to the work detail page
				except TimeoutException:
					driver.refresh()
			else:
				print "Wasn't an illustration or album! Maybe an animation?"

		# Move onto the next element
		retriesLeft = retries_allowed	# Grab global setting of allowed retries

		while retriesLeft+1 != 0 and mightBeLastPage:
			nextWorkElement = tryGrabbingElement(driver, 'css', pixiv_css_next_work)

			if nextWorkElement is not None: # Success :)
				try:
					nextWorkElement.click()
					mightBeLastPage = False
				except TimeoutException:
					# Thought it might be ready, but didn't work!
					print "Retrying to find the next work button. %s retries left..." % retriesLeft
					retriesLeft -= 1 # One retry taken!

					if retry_refresh:	# If we're serious, we can try refreshing...
						if workURL is not None:
							print "Trying returning to workURL %s" % workURL
							driver.get(workURL)	# Album failure, more effective to re-get workURL
						else:
							print "Trying refresh of current page %s" % driver.current_url
							driver.refresh()

			else: 													# Failed :(
				# Wasn't there, didn't work.
				print "Retrying to find the next work button. %s retries left..." % retriesLeft
				retriesLeft -= 1 # One retry taken!
				if retry_refresh:	# If we're serious, we can try refreshing...
					driver.refresh()

		if mightBeLastPage:
			# Retries exhausted, maybe we really have hit the end of the book...
			exhaustion = True

	print "Reached the end of Pixiv Book: \"%s\"" % bookName
	return [bookName, urlString]


# -------- COOKIES?!?!??! --------
#http://stackoverflow.com/questions/7854077/using-a-session-cookie-from-selenium-in-urllib2
def getDriverCookies(driver):	# Load driver_cookies from driver
	driver_cookies = driver.get_cookies()
	print "Got cookies, cookie size = %s." % str(len(driver_cookies))
	# print pp.pprint(driver_cookies)


def addRequestCookies():	# Load request_cookies into driver_cookies
	for cookie in driver_cookies:
		request_cookies[cookie["name"]]=cookie["value"]

	print "Loaded request cookies."


def addDriverCookies(driver): # Load driver_cookies into driver
	for cookie in driver_cookies:
		driver.add_cookie(cookie)


def loadCookiesFile(filePath):	# Load cookies file into driver_cookies
	if isfile(filePath):
		print 'Reading driver cookies from %s.' % filePath
		inFile = open(filePath, 'r')
		driver_cookies = eval(inFile.read())
		inFile.close()
		if len(driver_cookies) < 1:
			print "File found, but nothing in %s." % filePath
			return False # Got something, but it's empty

		return True
	else:
		print "Didn't find driver cookies in %s." % filePath
		return False


def saveCookiesFile(filePath):	# Write driver_cookies to file
	print 'Writing driver cookies to file.'
	inFile = open(filePath, 'w')
	inFile.write(str(driver_cookies))
	inFile.close()


def tryPixivCookies(driver):	# Attempt to load cookies from file
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
			print "Hey, you need to define your Pixiv login info into the two env vars:"
			print "$PIXIV_NAME and $PIXIV_PASS. Edit the pixiv.sh file in a text editor!"
			quit()

		driver.find_element_by_id(pixiv_id_login_name).send_keys(userName)
		driver.find_element_by_id(pixiv_id_login_pass).send_keys(passWord, Keys.RETURN)

		print "Logging in to Pixiv with %s" % (userName)
		sleep(3)

		# We're now logged in, let's save it.
		getDriverCookies(driver) # Save driver cookies to driver_cookies
		addRequestCookies() # Convert driver_cookies to request_cookies
		saveCookiesFile(cookies_file_path) # Write new driver_cookies to file for next run


# The main function. Starts with a string array of starting URLs.
def imageURLCrawler(urlList):
	# Start up Firefox
	print "Adblock xpi: %s\nAdblock profile: %s" % (adblock_xpi, profile_location)
	firefoxProfile = webdriver.FirefoxProfile(profile_location)
	firefoxProfile.add_extension(adblock_xpi)

	# Pixiv slow loading http://stackoverflow.com/a/22406998/3120546 fix??
	firefoxProfile.set_preference("webdriver.load.strategy", "unstable");

	driver = webdriver.Firefox(firefox_profile=firefoxProfile)
	driver.implicitly_wait(10) # ?? Tries anyway if the page keeps loading after 5 sec?

	outputDir = options.export
	if len(outputDir) == 0:
		print "WARNING: CANNOT HAVE A BLANK OUTPUT DIRECTORY. QUITTING."
		quit()

	# Print out some stuff.
	print "\n-------\nStarting image crawler..."
	if len(options.startURL) > 0:
		print "Starting URL: %s" % options.startURL
	if len(options.openList) > 0:
		print "Opening list file %s" % options.openList
	if options.writeFile:
		print "Writing image urls to file. View saved files in %s" % outputDir
	if options.download:
		print "Downloading images enabled. View saved files in %s" % outputDir
	if options.cbz:
		print "Downloading and archiving images enabled. View saved .cbz in %s" % outputDir
	elif options.zip:
		print "Downloading and archiving images enabled. View saved .zip in %s" % outputDir
	if options.dual:
		print "Dual page mode enabled."
	print "Set to download %s book(s)" % len(urlList)
	print "Throttle set to %s second(s).\n-------" % options.throttle

	pixivLoginNeeded = True
	bookNumber = 0
	bookName = ""
	# Book loop. If there are multiple books loaded, it'll do each one in this loop.
	for startURL in urlList:
		bookNumber += 1
		if len(startURL) == 0:
			print "Skipping blank URL."
			continue # Skip blank lines

		print "Viewing link %s of %s: %s" % (bookNumber, len(urlList), startURL)

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
			print "I don't think this link will work: %s" % startURL
			continue # Link isn't recognized, just move onto the next

		if bookName == "!@#$CONTINUE!@#$":
			# Using a dumb string because I moved code from this function into pururin() way later.
			continue # Gallery, restart the loop.


		### End of loop for this gallery
		# Write the archive file.
		if options.zip or options.cbz:
			if len(bookName) == 0:
				print "WARNING. BOOKNAME IS BLANK. CANNOT ARCHIVE %s. QUITTING." % outputDir + '/'
				quit()
			else:

				extension = 'zip' if options.zip else 'cbz'

				zipf = zipfile.ZipFile(outputDir + '/' + bookName + '.' + extension, 'w')
				createArchive(outputDir + '/' + bookName, zipf)
				zipf.close()

				print "Wrote archive \"%s\"" % (outputDir + '/' + bookName + '.' + extension)

				# If the download option isn't set, delete the download directory.
				if not options.download:
					rmtree(outputDir + '/' + bookName)

				else:
					print "Wrote to directory \"%s\"" % (outputDir + '/' + bookName + '/')

		# Write the output file.
		if options.writeFile and len(bookName) > 0:
			if not isdir(outputDir):
				mkdir(outputDir)

			outfile = open(outputDir + '/' + bookName + ".txt", 'w')
			outfile.write(urlString)
			outfile.close()
			print "Wrote to file \"%s\"" % (outputDir + '/' + bookName + ".txt")


		sleep(int(options.throttle)*2)


	### End of urlList for loop
	driver.quit()


#### Parser Stuff
parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL", default='', metavar="startURL")
parser.add_option("-o", "--openList", help="List file (\\n delimit)", default='', metavar="filename")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
parser.add_option("-g", "--gallery", help="Gallery page size", default='20', metavar="integer")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")
parser.add_option("-e", "--export", help="Export directory", default='output', metavar="string")
parser.add_option("-d", "--dual", help="Dual Page Mode", default=False, action="store_true")
parser.add_option("-w", "--writeFile", help="Write URLs to file", default=False, action="store_true")
parser.add_option("-l", "--download", help="Download images to directory", default=False, action="store_true")
parser.add_option("-z", "--zip", help="Create a zip file ...", default=False, action="store_true")
parser.add_option("-c", "--cbz", help="OR: Create a cbz file", default=False, action="store_true")

(options, args) = parser.parse_args()
# print "options:\n  %s\nargs:\n  %s" % (options, args)

urlList = []

# Open the list file (if one was specified)
if isfile(options.openList):
	listFile = open(options.openList, 'r')
	listContents = listFile.read()
	urlList = split(listContents, "\n")
	listFile.close()

# Append the startURL to the urlList
if len(options.startURL) > 0:
	urlList.append(options.startURL)

# Do it!
returnArray = imageURLCrawler(urlList)
print "-------\nDone!"