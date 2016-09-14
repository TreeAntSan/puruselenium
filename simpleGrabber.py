from optparse import OptionParser
from time import sleep
from os.path import isdir
from os import makedirs

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from requests import get


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

# Downloads an image and names it from a URL.
def imageDownloader(url, directory, referer=None):
  # Create the 'downloads' directory
  if not isdir(directory):
    makedirs(directory)

  imageFileName = url[url.rfind('/')+1:url.rfind('?')]
  if referer is not None:
    imageFileName = referer[referer.rfind('=')+1:].zfill(4) + '_' + imageFileName
  headers = {}

  # Download the image file
  if referer is not None:
    headers['referer'] = referer # Use referer to avoid possible scrape detectors

  r = get(url, headers=headers)

  # Write the image file
  imageFile = open(directory + '/' + imageFileName, 'w')
  imageFile.write(r.content)
  imageFile.close()

def start(url, directory, imageLocation, nextLocation):
  print "url: %s\ndirectory: %s\nimageLocation: %s\nnextLocation: %s\n" % (url, directory, imageLocation, nextLocation)
  sleep(1)

  driver = webdriver.Firefox()
  driver.get(url)

  keepGoing = True
  retryAvailable = False
  while keepGoing:
    imageLoc = imageLocation.split('>>')
    nextLoc = nextLocation.split('>>')

    imageElement = tryGrabbingElement(driver, imageLoc[0], imageLoc[1])
    nextElement = tryGrabbingElement(driver, nextLoc[0], nextLoc[1])

    if imageElement is None:
      print "No image found here.\nUrl: %s" % driver.current_url
      if not retryAvailable:
        keepGoing = False
      else:
        retryAvailable = False
        print "retry once"
        sleep(3)
        driver.get(driver.current_url)

    imageUrl = imageElement.get_attribute('src')
    print "Downloading %s" % imageUrl
    imageDownloader(imageUrl, directory, driver.current_url)

    sleep(1)
    if nextElement is None:
      keepGoing = False
      print "No next button visible. Done?\nUrl: %s" % driver.current_url
      if not retryAvailable:
        keepGoing = False
      else:
        retryAvailable = False
        print "retry once"
        sleep(3)
        driver.get(driver.current_url)


    nextElement.click()
    print "Clicking next button"
    retryAvailable = True


parser = OptionParser()
parser.add_option("-s", "--startURL", help="The starting URL", default='', metavar="startURL")
parser.add_option("-l", "--download", help="Download images to this directory", default='downloads', metavar="directory")
parser.add_option("-i", "--image", help="mode>>location", default='', metavar='string')
parser.add_option("-n", "--next", help="mode>>location", default='', metavar='string')
(options, args) = parser.parse_args()

start(options.startURL, options.download, options.image, options.next)


# div.entry-content>p>img
# span.nav-next>a