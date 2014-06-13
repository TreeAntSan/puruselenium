from optparse import OptionParser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys






parser = OptionParser()
parser.add_option("-f", "--file", help="The file to write", default="output.txt", metavar="FileLocation")
parser.add_option("-s", "--start", help="The starting URL \"http://www.example.com/page\"", default='http://www.example.com/page', metavar="startURL")
parser.add_option("-u", "--baseurl", help="The base URL of the site \"http://www.example.com\"", default='http://www.example.com', metavar="baseURL")

(options, args) = parser.parse_args()