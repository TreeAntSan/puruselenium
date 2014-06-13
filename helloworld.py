from selenium import webdriver

# Yeah, don't even need to run Selenium Server!

browser = webdriver.Firefox()
browser.get('http://seleniumhq.org/')
browser.quit()