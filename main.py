from PIL import Image, ImageDraw, ImageFont
import urllib2, StringIO, base64
from time import gmtime, strftime, time
from timeit import default_timer as timer
import RPi.GPIO as GPIO
import boto, csv, sys


# AMAZON S3 SETTINGS

keys = open('accessKeys.csv', 'r')
reader = csv.reader(keys)
reader.next()
BUCKET,_ ,ACCESS_KEY, SECRET_KEY = reader.next()
keys.close()
REGION_HOST = 's3-eu-central-1.amazonaws.com'

conn = boto.connect_s3(ACCESS_KEY, SECRET_KEY, host=REGION_HOST)
bucket = conn.get_bucket(BUCKET)

k = boto.s3.key.Key(bucket)

def percent_cb(complete, total):
    sys.stdout.write('<3')
    sys.stdout.flush()


# GPIO SETTINGS

PIN = 13

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(PIN, GPIO.FALLING, bouncetime=2000)


# CAMERA CLASS

class camera(object):
    def __init__(self,url,buffer):
        self.current = Image.new("L", (640,648) ,0)
        self.last = None
        self.url = url
        self.buffer_len = buffer
        self.buffer = []
        self.updateImage()


    def updateImage(self):
        self.buffer.append([strftime("%Y-%m-%d %H:%M:%S", gmtime()), self.getImage().convert("L")])
        if len(self.buffer) > self.buffer_len:
            self.buffer.pop(0)
            #self.last = self.current.copy()

    def getImage(self):
	try:
        	stream = urllib2.urlopen(self.url, timeout = 2)
        	bytes=''
        	while True:
            		bytes+=stream.read(1024)
            		a = bytes.find('\xff\xd8')
            		b = bytes.find('\xff\xd9')
            		if a!=-1 and b!=-1:
                		jpg = bytes[a:b+2]
                		bytes= bytes[b+2:]
                		return Image.open(StringIO.StringIO(jpg))
	except Exception, e:
		print "Error with camera %s" % self.url
		print e
		return Image.new("L", (360,360), 200)

from time import sleep
from subprocess import call

camera1 = camera("http://192.168.1.123:81/videostream.cgi?user=admin&pwd=888888",10)
camera2 = camera("http://192.168.1.120:81/videostream.cgi?user=admin&pwd=888888",10)
i=0

last_time = timer()

once = True

while True:

    if (timer() - last_time) > .5:
        camera1.updateImage()
        camera2.updateImage()
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

	crop_w = image_h  #int(image_w*0.8)
	
	cutoff = (image_w - crop_w) / 2	

	image1a = camera1.buffer[0][1].crop((cutoff,0,image_w-cutoff,image_h))
	image1b = camera1.buffer[-1][1].crop((cutoff,0,image_w-cutoff,image_h))
	image2a = camera2.buffer[0][1].crop((cutoff,0,image_w-cutoff,image_h))
	image2b = camera2.buffer[-1][1].crop((cutoff,0,image_w-cutoff,image_h))

        image_w, image_h = image1a.size

	scale = 3
	iscalew = int(image_w * scale)
	iscaleh = int(image_h * scale)

	print iscalew, iscaleh

	limage1a = image1a.resize((iscalew,iscaleh), Image.ANTIALIAS)
	limage1b = image1b.resize((iscalew,iscaleh), Image.ANTIALIAS)
	limage2a = image2a.resize((iscalew,iscaleh), Image.ANTIALIAS)
	limage2b = image2b.resize((iscalew,iscaleh), Image.ANTIALIAS)

	if once:
        	images_w, images_h = limage1a.size
        	canvas_w, canvas_h = canvas.size
        	centre_w = canvas_w/2
		imagepos_w = (centre_w / 2) - (images_w / 2)
		top = 500
		gap = 100
		once = False

        canvas.paste(limage1a,(imagepos_w,top))
        canvas.paste(limage1b,(imagepos_w,images_h+top+gap))
        canvas.paste(limage2a,(centre_w+imagepos_w,top))
        canvas.paste(limage2b,(centre_w+imagepos_w,images_h+top+gap))

	uid = str(int(time()))
	#base64.b16encode(strftime("%d%a%H%M%S", gmtime()))
	#print strftime("%a%H%M%S", gmtime())
        draw.text((imagepos_w,images_h+top), camera1.buffer[0][0], font = fnt)
        draw.text((imagepos_w,images_h*2+top+100), camera1.buffer[-1][0], font = fnt)
        draw.text((centre_w+imagepos_w,images_h+top), camera2.buffer[0][0], font = fnt)
        draw.text((centre_w+imagepos_w,images_h*2+top+100), camera2.buffer[-1][0], font = fnt)

        #canvas.save("%s_upload.jpg" % uid)

        
	tw, _ = draw.textsize(uid, font=fnt)
	uid_base16 = base64.b16encode(uid)
	draw.text((centre_w-(tw/2),canvas_h-200), uid_base16, font = fnt)

        canvas.save("%s_print.jpg" % uid)
	
        i = 0
	printout = "%s_print.jpg" % uid 
        call(['lp',printout])

        image1a.save("%s_1a.jpg" % uid)
        image1b.save("%s_1b.jpg" % uid)
        image2a.save("%s_2a.jpg" % uid)
        image2b.save("%s_2b.jpg" % uid)

	for img_up in ["%s_1a.jpg" % uid, "%s_1b.jpg" % uid, "%s_2a.jpg" % uid, "%s_2b.jpg" % uid]:
		k.key = img_up
		k.set_contents_from_filename(img_up, cb=percent_cb, num_cb=10)

        del draw
        del canvas
