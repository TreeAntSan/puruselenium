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
from os import getcwd
from time import sleep

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
thing()