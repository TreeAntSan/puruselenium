from optparse import OptionParser
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def doIt():
	browser = webdriver.Firefox()
	browser.get(options.startURL)
	sleep(5)




	browser.quit()





parser = OptionParser()
parser.add_option("-f", "--file", help="The file to write", default="output.txt", metavar="FileLocation")
parser.add_option("-s", "--startURL", help="The starting URL \"http://www.example.com/page\"", default="http://www.example.com/page", metavar="startURL")
parser.add_option("-u", "--baseURL", help="The base URL of the site \"http://www.example.com\"", default="http://www.example.com", metavar="baseURL")

(options, args) = parser.parse_args()
print "options:\n  %s\nargs:\n  %s" % (options, args)

# Do it!
doIt()