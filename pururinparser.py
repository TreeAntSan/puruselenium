# Standard
from optparse import OptionParser
from time import sleep
from string import rfind, split, capwords, replace, find, lower, strip
from re import sub
from os.path import isfile, isdir, join
from os import mkdir, makedirs, walk, getenv
from shutil import rmtree
import zipfile

# 3rd Party
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
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

#### XPath String Maintenance
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
pixiv_css_image_item = "li.image-item"
pixiv_id_login_name = "login_pixiv_id"
pixiv_id_login_pass = "login_password"
pixiv_id_login_submit = "login_submit"
pixiv_css_image_class = "img.original-image"

def directoryCleaner(directory):
	# Replace any potentially illegal characters with an underscore
	# These usually come from tags.

	# return sub('[^\w\-_\. ]', '_', directory) # Aggresive
	return sub('[\\\/:\*?"<>|]', '_', directory) # Relaxed


# Downloads an image and names it from a URL.
def imageDownloader(url, directory):
	# Create the 'downloads' directory
	if not isdir(directory):
		makedirs(directory)

	# Parse the image name from the url
	imageFileName = url[rfind(url,'/')+1:]
	imageFileName = fileNamePadder(imageFileName)

	# Download the image file
	r = get(url)

	# Write the image file
	imageFile = open(directory + '/' + imageFileName, 'w')
	imageFile.write(r.content)
	imageFile.close()


# Improves the filename by giving a padded number.
# CDisplay for Windows, for example, fails at ordering without them. (1, 11, 12,..., 19, 2, 20,...)
# Limits file names before number and extension to 50 characters
def fileNamePadder(fileName):
	return fileName[:rfind(fileName, '-')+1][:50] + fileName[rfind(fileName, '-')+1:rfind(fileName,'.')].zfill(3) + fileName[rfind(fileName,'.'):]


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
		return "!@#$CONTINUE!@#$"

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
					bookName = imageUrlA[rfind(imageUrlA, '/')+1:rfind(imageUrlA, '-')]

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
					imageDownloader(imageUrlA, outputDir + '/' + bookName)

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
					if imageUrlB != None:
						urlString += imageUrlB + "\n"
						pastImageUrlB = imageUrlB
						
						# Download imageUrlB
						if options.download or options.zip or options.cbz:
							imageDownloader(imageUrlB, outputDir + '/' + bookName)

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

		return bookName

def pixiv(driver, startURL, loginNeeded):
	# Go to the starting page!
	driver.get(startURL)
	

	# Wait, do we need to log in first?
	if loginNeeded:
		pixivLogin(driver)


	items = driver.find_element_by_css_selector(pixiv_css_image_item)

	print items
	return

def pixivLogin(driver):
	userName = getenv("PIXIV_NAME")
	passWord = getenv("PIXIV_PASS")
	print "Using %s:%s" % (userName, passWord)

	if len(userName) == 0 or len(passWord) == 0:
		print "Hey, you need to define your Pixiv login info into the two env vars:"
		print "$PIXIV_NAME and $PIXIV_PASS"
		quit()

	# driver.get("http://www.pixiv.net/")
	driver.find_element_by_id(pixiv_id_login_name).send_keys(userName)
	driver.find_element_by_id(pixiv_id_login_pass).send_keys(passWord, Keys.RETURN)
	# driver.find_element_by_id(pixiv_id_login_submit).click()


	# 
	
	print "I'd login with %s:%s" % (userName, passWord)

# The main function. Starts with a string array of starting URLs.
def imageURLCrawler(urlList):
	# Start up Firefox
	driver = webdriver.Firefox()

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

	pixivLoggedIn = False
	bookNumber = 0
	bookName = ""
	# Book loop. If there are multiple books loaded, it'll do each one in this loop.
	for startURL in urlList:
		bookNumber += 1
		if len(startURL) == 0:
			print "Skipping blank URL."
			continue # Skip blank lines

		print "Viewing link %s of %s: %s" % (bookNumber, len(urlList), startURL)

		if 'pururin' in startURL:
			bookName = pururin(driver, startURL, urlList, outputDir, bookNumber)
		if 'pixiv' in startURL:
			pixiv(driver, startURL, not pixivLoggedIn)
			sleep(5)

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