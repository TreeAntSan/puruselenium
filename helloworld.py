from selenium import webdriver
from time import sleep

# Yeah, don't even need to run Selenium Server!

browser = webdriver.Firefox()
browser.get('http://seleniumhq.org/')
sleep(5)
browser.quit()
