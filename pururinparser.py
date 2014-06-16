from optparse import OptionParser
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from os import path, makedirs
from string import rfind
#import wget

def doIt():
	driver = webdriver.Firefox()
	driver.get(options.startURL)

	# Parse page count from label
	# ofPagesElement = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[2]/span/label')
	# ofPagesText = ofPagesElement.text
	# print ofPagesText
	# ofPagesNumber = int(ofPagesText[rfind(ofPagesText)+1:])
	# oddPages = bool(ofPagesNumber%2)

	pagesPer = 1
	if options.dual:	# Switch to 'western' dual page mode
		doubleButton = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[2]/div[4]/a[2]')
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
			imageElementA = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[1]')
			imageUrlA = imageElementA.get_attribute('src')
			print imageUrlA
			urlString += imageUrlA + "\n"

		except NoSuchElementException:
			print "Reached end for \"%s\", got through %s pages." % (bookName, pagesPer*page)
			break


		# Deal with a second image element if in dual mode
		if options.dual:
			try:
				imageElementB = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img[2]')
				imageUrlB = imageElementB.get_attribute('src')
				if imageUrlB == pastB:
					# When there is just one image, this exception doesn't get thrown for some reason
					# So as a remedy, if the url is the same as the last time around, I throw it.
					raise NoSuchElementException()	

				print imageUrlB
				urlString += imageUrlB + "\n"
				pastB = imageUrlB

			except NoSuchElementException:
				print "Reached end for \"%s\", got through %s pages." % (bookName, (pagesPer*page)+1)
				break
			

		# Name the book from the last '/'+1 to the last '-'
		if len(bookName) == 0:
			bookName = imageUrlA[rfind(imageUrlA, '/')+1:rfind(imageUrlA, '-')]

		# Throttle the speed, otherwise Selenium will rip through pages a half-second a piece.
		sleep(throttle)

		# Click the next button.
		nextPageButton = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[1]/a[2]')
		nextPageButton.click()

	driver.quit()
	return [urlString, bookName]

parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL \"http://www.example.com/page\"", default="http://www.example.com/page", metavar="startURL")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
#parser.add_option("-w", "--download", help="Download in program", default=False, action="store_true")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")
parser.add_option("-d", "--dual", help="Dual Page Mode", default=False, action="store_true")
parser.add_option("-l", "--list", help="List file (\\n delimit)", default='', metavar="filename")

(options, args) = parser.parse_args()
print "options:\n  %s\nargs:\n  %s" % (options, args)

# Do it!
returnArray = doIt()
outfile = open(returnArray[1]+".txt", 'a')
outfile.write(returnArray[0])
