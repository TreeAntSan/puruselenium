from optparse import OptionParser
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from os import path, makedirs
from string import rfind

def doIt():
	driver = webdriver.Firefox()
	driver.get(options.startURL)

	throttle = int(options.throttle)
	pageLimit = int(options.pageLimit)
	downloadMode = options.download

	urlString = ""
	bookName = ""
	
	print "throttle %s pageLimit %s downloadMode %s" % (throttle, pageLimit, downloadMode)
	for page in range(pageLimit):
		try:
			imageElement = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[1]/a[2]/img')
		except NoSuchElementException:
			print "Reached end for \"%s\", got through %s pages." % (bookName, page)
			break


		imageUrl = imageElement.get_attribute('src')
		print imageUrl


		if len(bookName) == 0:
			bookName = imageUrl[rfind(imageUrl, '/')+1:-6]

		urlString += imageUrl + "\n"

		
		sleep(throttle)

		nextPageButton = driver.find_element_by_xpath('/html/body/div[2]/div[1]/div[2]/div/div[2]/div[1]/div[1]/a[2]')

		nextPageButton.click()
		sleep(throttle)


	driver.quit()





parser = OptionParser()
# parser.add_option("-f", "--file", help="The file to write", default="output.txt", metavar="FileLocation")
parser.add_option("-s", "--startURL", help="The starting URL \"http://www.example.com/page\"", default="http://www.example.com/page", metavar="startURL")
parser.add_option("-n", "--pageLimit", help="Only download n pages", default='9999', metavar="integer")
parser.add_option("-d", "--download", help="Download in program", default=False, action="store_true")
parser.add_option("-t", "--throttle", help="Seconds between pages", default='2', metavar="integer")

(options, args) = parser.parse_args()
print "options:\n  %s\nargs:\n  %s" % (options, args)

# Do it!
doIt()