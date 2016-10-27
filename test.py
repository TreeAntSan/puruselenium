try:
  from time import sleep
  from sys import version_info
  print("> We're gonna do some tests to see if things will likely work for you...")
  sleep(3)
  print("> If the program crashes, you need to look at what happened last and figure that's what broke it.")
  sleep(3)
  print("> Checking you have Python 3.5 or better!")
  sleep(2)
  if not version_info > (3,5,0):
    print("> Nope! But whatever, let's try anyway...")
  else:
    print("> Sweet! You do have 3.5 or better!")
  sleep(3)

  print("> Checking if you have selenium")
  sleep(2)
  from selenium import webdriver

  print("> Cool, you do! Let's do something!")
  sleep(2)
  browser = webdriver.Firefox()
  browser.get('http://seleniumhq.org/')
  sleep(5)
  browser.quit()
  print("> Neat, huh?")
  sleep(2)
  print("> Checking if you have requests")
  sleep(2)
  import requests

  print("> Cool, seems like you do!")
  sleep(2)
  print("> Okay, things should work... Bye bye!")
  sleep(2)

except Exception as e:
  print("> Whoops! Something broke! Here's what it said:\n{}".format(e))

quit()