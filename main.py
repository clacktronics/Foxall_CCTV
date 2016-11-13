from PIL import Image
import urllib
import StringIO

class camera(object):
    def __init__(self,url):
        self.current = Image.new("L", (640,648) ,0)
        self.last = None
        self.url = url
        self.updateImage()


    def updateImage(self):
        self.last = self.current.copy()
        stream = urllib.urlopen(self.url)
        bytes=''
        while True:
            bytes+=stream.read(1024)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                self.current = Image.open(StringIO.StringIO(jpg))
                break

from time import sleep

camera1 = camera("http://192.168.1.126:81/videostream.cgi?user=admin&pwd=&resolution=32&rate=0")

i=0

canvas = Image.new("L",(2480,3508),255)

while True:
    camera1.updateImage()
    canvas.paste(camera1.current,((2480/2)-640-20,10))
    canvas.paste(camera1.last,((2480/2)+20,10))
    canvas.save("image%03d.jpg" % i)
    print i
    i+=1
    sleep(1)
