from PIL import Image, ImageDraw, ImageFont
import urllib
import StringIO
from time import gmtime, strftime
from timeit import default_timer as timer
import RPi.GPIO as GPIO

PIN = 13

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(PIN, GPIO.FALLING, bouncetime=2000)

class camera(object):
    def __init__(self,url,buffer):
        self.current = Image.new("L", (640,648) ,0)
        self.last = None
        self.url = url
        self.buffer_len = buffer
        self.buffer = []
        self.updateImage()


    def updateImage(self):
        self.buffer.append([strftime("%Y-%m-%d %H:%M:%S", gmtime()), self.getImage()])
        if len(self.buffer) > self.buffer_len:
            self.buffer.pop(0)
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

camera1 = camera("http://192.168.1.112:81/videostream.cgi?user=admin&pwd=&resolution=32&rate=0",10)

i=0

last_time = timer()

while True:

    if (timer() - last_time) > 1:
        camera1.updateImage()
        i+=1
        print camera1.buffer[-1][0]
        last_time = timer()

    # print "----"
    # for l in camera1.buffer:
    # print l
    # print "----"

    if  GPIO.event_detected(PIN):
        print "export"
        canvas = Image.new("L",(2480,3508),255)
        draw = ImageDraw.Draw(canvas)
        fnt = ImageFont.truetype('DejaVuSansMono.ttf', 40)

        image_w, image_h = camera1.buffer[-1][1].size
        canvas_w, canvas_h = canvas.size
        centre_w = canvas_w/2

        canvas.paste(camera1.buffer[0][1],(centre_w-image_w-100,100))
        canvas.paste(camera1.buffer[-1][1],(centre_w+100,100))

        draw.text((centre_w-image_w-100,image_h+100), camera1.buffer[0][0], font = fnt)
        draw.text((centre_w+100,image_h+100), camera1.buffer[-1][0], font = fnt)

        canvas.save("image.jpg")
        del draw
        del canvas
        i = 0
        call(['lp','image.jpg'])
