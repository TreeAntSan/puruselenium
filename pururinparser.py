from optparse import OptionParser
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from string import rfind
from string import split
from os.path import isfile
#import wget

#### Intro
# This tool is in Python (written in 2.7.3) written in Summer 2014
# The only extra library it uses is pypi Selenium, which can be found here:
# https://pypi.python.org/pypi/selenium
# Download Python 2.7.X (whatever is current X), figure out how to get
# command line access, navigate your terminal to the location
# of this program, run "python pururinparser.py --help"
# Basically, take this, take the URLs into a txt file, open in Firefox, and
# use the plugin DownThemAll! (it's a trustworthy plugin) to download them.
# DTA may need an option checked to read from plain text. Be sure to self-throttle
# your downloads or fear an IP ban.
# Starting page can be either the first page OR the gallery. Book name is determined
# by the name of the first page image.


#### Maintenance
# If things stop working. Get the plugin Firebug for Firefox, open it, navigate
# to a page, and use the Blue-Arrow-In-Box tool to investigate an element. Click it,
# then in list right click the hi-lited area and select "copy XPath".
# Replace the text in the variables below with that text (remember the single quotes!)
xpath_doubleButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[4]/a[2]' # WESTERN ORDER!!!
xpath_imageElementA = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[1]'
xpath_imageElementB = '/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[2]'
xpath_nextPageButton = '/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[1]/a[2]'
xpath_galleryFirstPage = '/html/body/div[2]/div[1]/div/div/div[1]/div/div[3]/ul/li[1]/a/img[1]'


def imageURLCrawler(startArray):
	driver = webdriver.Firefox()

	for startURL in startArray:
		driver.get(startURL)

		try:
			galleryFirstPage = driver.find_element_by_xpath(xpath_galleryFirstPage)
			galleryFirstPage.click()
		except NoSuchElementException:
			pass # Do nothing, we coo.

		pagesPer = 1
		if options.dual:	# Switch to 'western' dual page mode
			sleep(2) # Sometimes this comes in slow
			doubleButton = driver.find_element_by_xpath(xpath_doubleButton)
			doubleButton.click()
			pagesPer = 2
			print "Using double page mode."

		throttle = int(options.throttle)
		pageLimit = int(options.pageLimit)
		# downloadMode = options.download

		urlString = ""
		bookName = ""
		pastB = "" # Work around for uneven pages in dual mode.

		for page in range(pageLimit):

			# Deal with the image element
			try:
				imageElementA = driver.find_element_by_xpath(xpath_imageElementA)
				imageUrlA = imageElementA.get_attribute('src')
				print imageUrlA
				urlString += imageUrlA + "\n"

			except NoSuchElementException:
				print "Reached end for \"%s\", got through around %s pages." % (bookName, pagesPer*page)
				break


			# Deal with a second image element if in dual mode
			if options.dual:
				try:
					imageElementB = driver.find_element_by_xpath(xpath_imageElementB)
					imageUrlB = imageElementB.get_attribute('src')
					if imageUrlB == pastB:
						# When there is just one image, this exception doesn't get thrown for some reason
						# So as a remedy, if the url is the same as the last time around, I throw it.
						raise NoSuchElementException()	

					# When there are double-wide images, the site automatically shows only one image.
					# It fails in a special way with imageUrlB == None, so if I see this, we'll side step
					# the need to grab imageUrlB this time.
					if imageUrlB != None:
						print imageUrlB
						urlString += imageUrlB + "\n"
						pastB = imageUrlB
					else:
						page -= 1

				except NoSuchElementException:
					print "Reached end for \"%s\", got through around %s pages." % (bookName, (pagesPer*page)+1)
					break
				

			# Name the book from the last '/'+1 to the last '-'
			if len(bookName) == 0:
				bookName = imageUrlA[rfind(imageUrlA, '/')+1:rfind(imageUrlA, '-')]

			# Throttle the speed, otherwise Selenium will rip through pages a half-second a piece.
			sleep(throttle)

			# Click the next button.
			nextPageButton = driver.find_element_by_xpath(xpath_nextPageButton)
			nextPageButton.click()

		### End of loop for this gallery
		sleep(throttle*2)


	### End of startArray for loop
	driver.quit()
	return [urlString, bookName]

parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL \"http://www.example.com/page\"", default='', metavar="startURL")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")
parser.add_option("-d", "--dual", help="Dual Page Mode", default=False, action="store_true")
parser.add_option("-w", "--writeFile", help="Write URLs to file", default=False, action="store_true")
parser.add_option("-o", "--openList", help="List file (\\n delimit)", default='', metavar="filename")
#parser.add_option("-l", "--download", help="Download in program", default=False, action="store_true")

(options, args) = parser.parse_args()
# print "options:\n  %s\nargs:\n  %s" % (options, args)

startArray = []

# Open the list file (if one was specified)
if isfile(options.openList):
	listFile = open(options.openList, 'r')
	listContents = listFile.read()
	startArray = split(listContents, "\n")

# Append the startURL to the startArray
if len(options.startURL) > 0:
	startArray.append(options.startURL)

# Do it!
returnArray = imageURLCrawler(startArray)

if options.writeFile:
	# Write the output file.
	outfile = open(returnArray[1]+".txt", 'a')
	outfile.write(returnArray[0])
	print "Wrote to file \"%s\"" % (returnArray[1]+".txt")
