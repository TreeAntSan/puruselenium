from time import sleep
mylist = ['one', 'gallery', 'three', 'gallery', 'four', 'five', 'gallery']
insert = ['1', '2', '3']
number = 0
for item in mylist:
	number +=1
	if item == 'gallery':
		print 'trigger!'
		mylist[number:number] = insert
		
		continue
	print item
	sleep(1)