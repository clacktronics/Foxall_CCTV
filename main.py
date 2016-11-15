from PIL import Image
import urllib
import StringIO

class camera(object):
    def __init__(self,url,buffer):
        self.current = Image.new("L", (640,648) ,0)
        self.last = None
        self.url = url
	self.buffer_len = buffer
	self.buffer = []
        self.updateImage()


    def updateImage(self):
	self.buffer.append(self.getImage())
        if len(self.buffer) > self.buffer_len:
		self.buffer.pop()
	#self.last = self.current.copy()
        
    def getImage(self):
	stream = urllib.urlopen(self.url)
        bytes=''
        while True:
            bytes+=stream.read(1024)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                return Image.open(StringIO.StringIO(jpg))

from time import sleep
from subprocess import call

camera1 = camera("http://192.168.1.112:81/videostream.cgi?user=admin&pwd=&resolution=16&rate=0",10)

i=0

canvas = Image.new("L",(2480,3508),255)

while True:
    camera1.updateImage()
    i+=1
    print "----"
    for l in camera1.buffer:
	print l
    print "----"
    if i > 10:
	print "a"
    	canvas.paste(camera1.buffer[-1],((2480/2)-640-20,10))
    	canvas.paste(camera1.buffer[0],((2480/2)+20,10))
    	canvas.save("image.jpg")
	i = 0
	#call(['lp','image.jpg'])
    sleep(1)
