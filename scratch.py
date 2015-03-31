# from time import sleep
# mylist = ['one', 'gallery', 'three', 'gallery', 'four', 'five', 'gallery']
# insert = ['1', '2', '3']
# number = 0
# for item in mylist:
# 	number +=1
# 	if item == 'gallery':
# 		print 'trigger!'
# 		mylist[number:number] = insert
		
# 		continue
# 	print item
# 	sleep(1)


from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from os import getcwd, getenv
from time import sleep
import sys

googleImageCss = "img#hplogo"

def thing():
	driverProfile = webdriver.FirefoxProfile()
	#https://selenium-python.readthedocs.org/en/latest/faq.html?highlight=profile
	driverProfile.set_preference("browser.download.folderList",2)
	driverProfile.set_preference("browser.download.manager.showWhenStarting",False)
	# driverProfile.set_preference("browser.download.useDownloadDir",False)
	driverProfile.set_preference("browser.download.dir", getcwd())
	driverProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg,image/png,image/gif")
	# driverProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg")
	# driverProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/png")
	# driverProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/gif")
	# driverProfile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")


	driver = webdriver.Firefox(firefox_profile=driverProfile)


	# driver = webdriver.Firefox()
	driver.get('http://google.com')
	logo = driver.find_element_by_css_selector(googleImageCss)
	logo.click()
	cwd = getcwd()
	print "I'm in: %s" % cwd

	fullSavePath = cwd + '/' + 'goog.png'

	# ActionChains(driver).context_click(logo).send_keys('v').send_keys(Keys.CONTROL, 'a').send_keys(fullSavePath).send_keys(Keys.RETURN).send_keys(Keys.RETURN).perform()
	ActionChains(driver).context_click(logo).send_keys('v').perform()
	ActionChains(driver).send_keys(Keys.ENTER).perform()
	# ActionChains(driver).context_click(logo).send_keys('v').perform()
	# sleep(2) # wait a second for the save dialog to show
	# ActionChains(driver).send_keys(Keys.CONTROL, 'a').send_keys(fullSavePath).perform()
	# sleep(2) # wait a second for the save dialog to show
	# ActionChains(driver).send_keys(Keys.RETURN).send_keys(Keys.RETURN).perform()

	# driver.context_click(logo)
	# driversend_keys('v')
	# driver.send_keys(Keys.CONTROL, 'a')
	# driver.send_keys(fullSavePath)
	# driver.send_keys(Keys.RETURN)
	# driver.send_keys(Keys.RETURN)


def pixivLogin(driver):
	userName = getenv("PIXIV_NAME")
	passWord = getenv("PIXIV_PASS")
	print "Using %s:%s" % (userName, passWord)

	if len(userName) == 0 or len(passWord) == 0:
		print "Hey, you need to define your Pixiv login info into the two env vars:"
		print "$PIXIV_NAME and $PIXIV_PASS. Edit the pixiv.sh file in a text editor!"
		quit()
	pixiv_id_login_name = "login_pixiv_id"
	pixiv_id_login_pass = "login_password"
	driver.find_element_by_id(pixiv_id_login_name).send_keys(userName)
	driver.find_element_by_id(pixiv_id_login_pass).send_keys(passWord, Keys.RETURN)
	
	print "Logging in to Pixiv with %s, %s" % (userName, passWord)

def pixivtest():

	pixiv_xpath_first_image_item = "//li[@class='image-item ']/a[1]"
	# pixiv_xpath_work_title = "//div[@class='ui-expander-target']/h1"
	pixiv_xpath_work_title = "/html/body/div[6]/div[2]/div[1]/div/section[1]/div/h1"
	pixiv_css_work_title = "div[class=ui-expander-target]>h1[class^=title]"

	driver = webdriver.Firefox()
	driver.get("http://www.pixiv.net/member_illust.php?id=438303")
	pixivLogin(driver)
	driver.find_element_by_css_selector(pixiv_xpath_first_image_item).click()

	
	title = driver.find_element_by_id(pixiv_css_work_title)
	print title.text

# thing()
# pixivtest()

def pixivJumpLink(url):
	jumpPos = url.rfind('>>')	if url.rfind('>>') != -1 else None
	firstPos = url.rfind('<<')	if url.rfind('<<') != -1 else None


	jumpNum = url[jumpPos+2:firstPos] if jumpPos > 0 else None
	firstNum = url[firstPos+2:] if firstPos > 0 else None
	
	strip = jumpPos if jumpPos is not None else firstPos
	print "\noriginal: %s" % url
	print   "stripped: %s\n" % url[:strip]
	print "jump: %s" % jumpNum
	print "first: %s" % firstNum
	
	

fullLink = "http://www.pixiv.net/member_illust.php?id=XXXX>>23<<3"
jumpLink = "http://www.pixiv.net/member_illust.php?id=XXXX>>23"
startLink = "http://www.pixiv.net/member_illust.php?id=XXXX<<3"
normalLink = "http://www.pixiv.net/member_illust.php?id=XXXX"

# pixivJumpLink(fullLink)
# pixivJumpLink(jumpLink)
# pixivJumpLink(startLink)
# pixivJumpLink(normalLink)

def loop(retriesAllowed, triesNeeded, pagesTotal):
	
	page = 1	# virtual
	tries = 1	# virtual
	exhaustion = False

	while not exhaustion:
		retriesLeft = retriesAllowed
		mightBeLastPage = True
		print "-------SECRET PAGE ACTIVITY THAT NEEDS TO RUN"



		# print "trying page %s" % str(page)
		while retriesLeft+1 != 0 and mightBeLastPage:
			print "try page#%s attempt #%s" % (page, tries)

			# SECRET END OF BOOK LOGIC
			if page > pagesTotal:
				triesNeeded = 999; # Absolute end


			# SUCCESS
			if tries == triesNeeded: # Secret trigger that makes it work
				print "successful on page #%s, triesNeeded=%s" % (page,triesNeeded)
				# retriesLeft = retriesAllowed # Reset retries
				page += 1 # Click next page
				tries = 1 # Reset tries for next page
				sleep(1)
				mightBeLastPage = False

			# FAILED
			else:

				sleep(1)
				print "failed on page #%s" % page
				print "retries left: %s" % retriesLeft
				retriesLeft -= 1 # Close to giving up
				tries += 1 # Getting closer
				# continue

		if mightBeLastPage:
			sys.stdout.write("true exhaustion")
			exhaustion = True
	print('->exit')


	# while not exhaustion:
	# 	# print "trying page %s" % str(page)
	# 	while retriesLeft+1 != 0:
	# 		print "try page#%s attempt #%s" % (page, tries)

	# 		# SUCCESS
	# 		if tries == triesNeeded: # Secret trigger that makes it work
	# 			if page < pagesTotal: # Really the end, for real.
	# 				print "successful on page #%s, triesNeeded=%s" % (page,triesNeeded)
	# 				retriesLeft = retriesAllowed # Reset retries
	# 				page += 1 # Click next page
	# 				tries = 1 # Reset tries for next page
	# 				sleep(1)
	# 			else:
	# 				break # Really done

	# 		# FAILED
	# 		else:

	# 			sleep(1)
	# 			print "failed on page #%s" % page
	# 			print "retries left: %s" % retriesLeft
	# 			retriesLeft -= 1 # Close to giving up
	# 			tries += 1 # Getting closer
	# 			continue

	# 	sys.stdout.write("true exhaustion")
	# 	exhaustion = True
	# print('->exit')

loop(3, 3, 3)