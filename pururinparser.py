# Standard
from optparse import OptionParser
from time import sleep
from string import rfind, split, capwords, replace, find, lower, strip
from re import sub
from os.path import isfile, isdir, join
from os import mkdir, makedirs, walk
from shutil import rmtree
import zipfile

# 3rd Party
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from requests import get

#### Intro
# This tool is in Python (written in 2.7.3) written in Summer 2014

# The two libraries it uses is pypi Selenium, which can be found here:
# https://pypi.python.org/pypi/selenium
# And Requests, which can be found here:
# http://docs.python-requests.org/en/latest/index.html

# Download Python 2.7.X (whatever is current X), figure out how to get
# command line access, navigate your terminal to the location
# of this program, run "python pururinparser.py --help"

# Basically, take this, take the URLs into a txt file, open in Firefox, and
# use the plugin DownThemAll! (it's a trustworthy plugin) to download them.
# DTA may need an option checked to read from plain text. Be sure to self-throttle
# your downloads or fear an IP ban.

# Starting page can be either the first page OR the gallery. Book name is determined
# by the name of the first page image.

# You can even import a txt file with the starting URL for each book you want.
# Just paste the full http:// link onto a single line byitself, nothing else.

# This will create zip/cbz files for you as an option. They are not compressed.

#### XPath String Maintenance
# If things stop working. Get the plugin Firebug for Firefox, open it, navigate
# to a page, and use the Blue-Arrow-In-Box tool to investigate an element. Click it,
# then in list right click the hi-lited area and select "copy XPath".
# Replace the text in the variables below with that text (remember the single quotes!)
xpath_doubleButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[4]/a[2]' # WESTERN ORDER!!!
xpath_imageElementA = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[1]'
xpath_imageElementB = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[2]'
xpath_nextPageButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[1]/a[2]'
xpath_galleryFirstPage = "//ul[@class='thumblist']/li[1]/a/img[1]"
xpath_tableInfo = "//table[@class='table-info']"


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
			xpath_tagCheck = xpath_tableInfo + '/tbody/tr[%s]/td[%s]%s'
			tagElement = driver.find_element_by_xpath(xpath_tagCheck % (x, '1', ''))
			if find(lower(tagElement.text), lower(desiredTagName)) != -1:
				tagValueElement = driver.find_element_by_xpath(xpath_tagCheck % (x, '2', '/ul/li/a'))
				return directoryCleaner(tagValueElement.text) # Remove any illegal characters
		except NoSuchElementException:
			if (x == 1):
				break # If this broke on the first time, then just give up - wrong page.
			pass # Do nothing, we coo.

	return '' # Didn't get the tag.


# The main function. Starts with a string array of starting URLs.
def imageURLCrawler(startArray):
	# Start up Firefox
	driver = webdriver.Firefox()

	outputDir = options.export

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
	print "Set to download %s book(s)" % len(startArray)
	print "Throttle set to %s seconds.\n-------" % options.throttle

	bookNumber = 0
	# Book loop. If there are multiple books loaded, it'll do each one in this loop.
	for startURL in startArray:
		bookNumber += 1
		if len(startURL) == 0:
			print "Skipping blank URL."
			continue # Skip blank lines

		print "Downloading book %s of %s" % (bookNumber, len(startArray))
		print "Downloading book located at %s" % startURL		

		# Go to the starting page!
		driver.get(startURL)

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
			galleryFirstPage = driver.find_element_by_xpath(xpath_galleryFirstPage)
			galleryFirstPage.click()
		except NoSuchElementException:
			pass # Do nothing, we coo.

		pagesPer = 1
		if options.dual:	# Switch to 'western' dual page mode
			for x in range(10):	# Sometimes this loads in slow, so we try 10 times with 1 sec rests
				try:
					doubleButton = driver.find_element_by_xpath(xpath_doubleButton)
					doubleButton.click()
					pagesPer = 2
					break	# It worked! Break from the loop.
				except NoSuchElementException:
					sleep(1) # It didn't work! Rest for a second
			
		throttle = int(options.throttle)
		pageLimit = int(options.pageLimit)

		urlString = ""
		bookName = ""
		pastImageUrlA = "" # Prevent situations where it'll infinitely redownload one page.
		pastImageUrlB = "" # Work around for uneven pages in dual mode.

		for page in range(pageLimit):

			# Deal with the image element
			try:
				imageElementA = driver.find_element_by_xpath(xpath_imageElementA)
				imageUrlA = imageElementA.get_attribute('src')
				
				if imageUrlA != pastImageUrlA:
					urlString += imageUrlA + "\n"
					
					# Name the book from the last '/'+1 to the last '-'
					if len(bookName) == 0:
						bookName = imageUrlA[rfind(imageUrlA, '/')+1:rfind(imageUrlA, '-')]

						# Format it nice. 'book-title-thing' becomes 'Book Title Thing'
						bookName = replace(capwords(bookName, '-'), '-', ' ')

						# Add the artist name to front if available (start from Gallery Page)
						if len(artistName) > 0:
							bookName = artistName + ' - ' + bookName

						# Add first parody to front if available (start from Gallery Page)
						if len(parodyTag) > 0:
							bookName = parodyTag + ' - ' + bookName

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
					imageElementB = driver.find_element_by_xpath(xpath_imageElementB)
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
			sleep(throttle)

			# Click the next button.
			nextPageButton = driver.find_element_by_xpath(xpath_nextPageButton)
			nextPageButton.click()


		### End of loop for this gallery
		# Write the archive file.
		if options.zip or options.cbz:
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

		
		sleep(throttle*2)


	### End of startArray for loop
	driver.quit()


#### Parser Stuff
parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL", default='', metavar="startURL")
parser.add_option("-o", "--openList", help="List file (\\n delimit)", default='', metavar="filename")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")
parser.add_option("-e", "--export", help="Export directory", default='output', metavar="string")
parser.add_option("-d", "--dual", help="Dual Page Mode", default=False, action="store_true")
parser.add_option("-w", "--writeFile", help="Write URLs to file", default=False, action="store_true")
parser.add_option("-l", "--download", help="Download images to directory", default=False, action="store_true")
parser.add_option("-z", "--zip", help="Create a zip file ...", default=False, action="store_true")
parser.add_option("-c", "--cbz", help="OR: Create a cbz file", default=False, action="store_true")

(options, args) = parser.parse_args()
# print "options:\n  %s\nargs:\n  %s" % (options, args)

startArray = []

# Open the list file (if one was specified)
if isfile(options.openList):
	listFile = open(options.openList, 'r')
	listContents = listFile.read()
	startArray = split(listContents, "\n")
	listFile.close()

# Append the startURL to the startArray
if len(options.startURL) > 0:
	startArray.append(options.startURL)

# Do it!
returnArray = imageURLCrawler(startArray)
print "-------\nDone!"