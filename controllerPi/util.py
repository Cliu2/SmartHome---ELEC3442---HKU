import socket
from sense_hat import SenseHat
import pygame
from pygame.locals import *
import RPi.GPIO as GPIO
import atexit
import _thread as thread
import io
import struct
import time
import picamera
from neopixel import *
from buzzer__mario import *
import serial

GPIO.setmode(GPIO.BCM)
class Server():
    def __init__(self,PORT=12345):
        print("serv")
        self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind(('',PORT))
        print('Server created.')
        self.waitConnection()

    def closeServer(self):
        print('Server closed.')
        self.server.close()

    def waitConnection(self):
        self.server.listen(1)
        con,addr=self.server.accept()
        self.con=con
        print('Connected to %s:%s.' % (addr[0],addr[1]))

    def sendMsg(self,msg):
        self.con.send(msg.encode())

    def receiveMsg(self):
        #the message in terms of an array of words
        msg=self.con.recv(1024).decode().split(' ')
        return msg

class Client():
    def __init__(self,SERVER_IP, PORT=12345):
        print("here")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((SERVER_IP, PORT))
        print('Server connected')
        self.server=server
        
    def sendMsg(self,msg):
        self.server.send(msg.encode())

    def receiveMsg(self):
        msg=self.server.recv(1024).decode()
        return msg
        
class senseHat():
    def __init__(self):
        sense=SenseHat()
        sense.clear()
        pygame.init()
        pygame.display.set_mode((640, 480))
        self.sense=sense
        self.pygame=pygame
        
    def getTemp(self,repeat=1):
        res=[]
        for r in reapeat:
            temp1=self.sense.get_temperature_from_humidity()
            temp2=self.sense.get_temperature_from_pressure()
            res.append((temp1+temp2)/2)
        return sum(res)/len(res)
        
    def getHumid(self,repeat=1):
        res=[]
        for r in reapeat:
            hum=self.sense.get_humidity()
            res.append(hum)
        return sum(res)/len(res)

    def getPres(self,repeat=1):
        res=[]
        for r in reapeat:
            pre=self.sense.get_pressure()
            res.append(pre)
        return sum(res)/len(res)
    
    def setPixel(self,x,y,r,g,b):
        if x not in range(0,7) or y not in range(0,7):
            print("pixel not in range!")
            return
        self.sense.set_pixel(x,y,r,g,b)

    def setPixels(self,pixels):
        #pixels: a list of 64 elements, each is a list of [r,g,b]
        if len(pixels)!=64 or len(pixels[0])!=3:
            print("pixels array shape wrong!")
            return
        self.sense.set_pixels(pixels)

class FanSet():
    def __init__(self,pins=[2,3,4]):
        self.pins=pins
        for pin in pins:
            GPIO.setup(pin,GPIO.OUT)
        self.switchAll(True)

    def switch(self,index,status):
        pin=self.pins[index]
        GPIO.output(pin,status)

    def switchAll(self,status):
        for pin in self.pins:
            
            if pin==2:
                status=not status
            GPIO.output(pin,status)
            
    def turnON(self,index):
        self.switch(index,False)
        
    def turnOFF(self,idx):
        self.switch(idx,True)
        
    def turnAllON(self):
        self.switchAll(False)
        
    def turnAllOFF(self):
        self.switchAll(True)

class Humidifier():
    def __init__(self,pin=6):
        self.pin=pin
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,0)
        
    def switch(self):
        GPIO.output(self.pin,1)
        time.sleep(0.10)
        GPIO.output(self.pin,0)
        
class Heater():
    def __init__(self,pin=5,OnLastTime=7):
        self.pin=pin
        self.ontime=OnLastTime
        self.lastOnTime=None
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,0)

    def switch(self,status):
        pin=self.pin
        GPIO.output(pin,status)
""" SOME SAFEGUARD, ALLOW HEAT UP FOR 7S EVERY 10S
        if status==0:
            GPIO.output(pin,status)
        else:
            curTime=time.time()
            if curTime-self.lastOnTime>10:
                thread.start_new_thread(self.turnOn)
                self.lastOnTime=curTime
            else:
                thread.start_new_thread(turnOnAfter,self.lastOnTime+10-curTime)

    def turnOn(self):
        GPIO.output(self.pin,1)
        startTime=time.time()
        while True:
            curTime=time.time()
            if curTime-startTime>self.ontime:
                GPIO.output(self.pin,0)

    def turnOnAfter(self,waitTime):
        time.sleep(waitTime)
        self.turnOn()
"""

class Water():
    def __init__(self,pin=7):
        self.pin=pin
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,0)

    def switch(self,status):
        pin=self.pin
        GPIO.output(pin,status)
                
class CameraClient():
    def __init__(self,address,port=12346):
        #connect to server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(10):
            try:  
                client_socket.connect((address, port))
                break
            except Exception as e:
                time.sleep(1)
        connection = client_socket.makefile('wb')
        print("Connect to server:",address," ,at port:",port)
        self.connection=connection
        self.client_socket=client_socket
        thread.start_new_thread(self.streaming,())
        
    def streaming(self):
        connection=self.connection
        client_socket=self.client_socket
        try:
            with picamera.PiCamera() as camera:
                camera.resolution = (320, 240)      # pi camera resolution
                camera.framerate = 15               # 15 frames/sec
                time.sleep(2)                       # give 2 secs for camera to initilize
                start = time.time()
                stream = io.BytesIO()
                
                # send jpeg format video stream
                for foo in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
                    connection.write(struct.pack('<L', stream.tell()))
                    connection.flush()
                    stream.seek(0)
                    connection.write(stream.read())
                    if time.time() - start > 600:
                        break
                    stream.seek(0)
                    stream.truncate()
            connection.write(struct.pack('<L', 0))                       
        finally:
            connection.close()
            client_socket.close()
            
    def end(self):
        self.connection.close()
        self.client_socket.close()
        
class CameraServer():
    def __init__(self,host,port):
        self.server_socket = socket.socket()
        self.server_socket.bind((host, port))
        self.waitConnection()
        
    def waitConenction(self):
        self.server_socket.listen(0)
        self.connection, self.client_address = self.server_socket.accept() 
        print("Host: ", self.host_name + ' ' + self.host_ip)
        print("Connection from: ", self.client_address)
        self.connection = self.connection.makefile('rb')
        self.host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(self.host_name)
        self.keepConnect=True
        thread.start_new_thread(self.streaming,())
        
    def streaming(self): 
        try:         
            # need bytes here
            stream_bytes = b' '
            while self.keepConnect:
                stream_bytes += self.connection.read(1024)
                first = stream_bytes.find(b'\xff\xd8')
                last = stream_bytes.find(b'\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last + 2]
                    stream_bytes = stream_bytes[last + 2:]
                    self.image = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    cv2.imshow('image', self.image)
        finally:
            self.connection.close()
            self.server_socket.close()
            
    def capturePicture(self):
        return self.image
            
    def end(self):
        self.keepConnect=False


class Bluetooth():
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyS0", baudrate=9600)

    def readword(self):
        data=''
        while True:
            t=self.ser.read().decode()
            if t=='*':
              data=''
            elif t=='#':
              return data
            else:
              data+=t
              print(data)

class Buzzer():
    def __init__(self,pin=23):
        self.pin=pin
        GPIO.setup(self.pin, GPIO.OUT)
        

    def ring(self):
        while True:
            tone1 = GPIO.PWM(self.pin, 600)
            tone1.start(80)
            time.sleep(1) 
            tone1.stop()
            tone1 = GPIO.PWM(self.pin, 220)
            tone1.start(80)
            time.sleep(1) 
            tone1.stop()

        
    def mario(self):
        play(underworld_melody,underworld_tempo,0.800)     
        destroy()
    
    def theme (self):
        play(melody,tempo,0.800)
        destroy()


class Curtain():
    def __init__(self,pin=17):
        self.pin=pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.pin, 50) # GPIO 17 for PWM with 50Hz
        self.servo.start(2.5) # Initialization
        self.servo.ChangeDutyCycle(0)
        
    def switchMode(self,mode):
        #mode: UP|DOWN
        if mode=='UP':
            thread.start_new_thread(self.UP,())
        elif mode=='DOWN':
            thread.start_new_thread(self.DOWN,()) 

    def UP(self):
        self.servo = GPIO.PWM(self.pin, 50) # GPIO 17 for PWM with 50Hz
        self.servo.start(2.5) # Initialization
        c=1.7
        self.servo.ChangeDutyCycle(c)
        print(c)
        time.sleep(5)
        self.servo.ChangeDutyCycle(0)

    def DOWN(self):
        self.servo = GPIO.PWM(self.pin, 50) # GPIO 17 for PWM with 50Hz
        self.servo.start(2.5) # Initialization
        c=7.5
        self.servo.ChangeDutyCycle(c)
        print(c)
        time.sleep(6)
        self.servo.ChangeDutyCycle(0)

class LED():
    def __init__(self,pin=18):
        # LED strip configuration:
        LED_COUNT      = 30      # Number of LED pixels.
        LED_PIN        = pin      # GPIO pin connected to the pixels (18 uses PWM!).
        #LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
        LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
        LED_BRIGHTNESS = 0     # Set to 0 for darkest and 255 for brightest
        LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
        LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
        n=0
        self.interrupt=False
        #start LED
        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()

    def switchMode(self,mode):
        #mode: bedtime|sunlight
        if mode=='bedtime':
            thread.start_new_thread(self.bedtime,())
        elif mode=='sunlight':
            thread.start_new_thread(self.sunlight,())
        elif mode=='ON':
            self.interrupt=True
            for i in range(30):
                self.strip.setBrightness(60)
                self.strip.setPixelColorRGB( i, 171, 227, 81)
            self.strip.show()
        elif mode=='OFF':
            self.interrupt=True
            for i in range(30):
                self.strip.setBrightness(0)
                self.strip.setPixelColorRGB( i, 0, 0, 0)
            self.strip.show()

    def bedtime(self):
        strip=self.strip
        self.interrupt=False
        try:
            brightness=strip.getBrightness()
#            bed_start_time=time.time()
            while not self.interrupt:
                strip.setBrightness(brightness)
                
                if brightness>0:
                    brightness = brightness - 1
##                    print(brightness)
                    for i in range(30):
                        strip.setPixelColorRGB( i, 171, 227, 81)
                        i=i+1
                    strip.show()
                    time.sleep(0.0001)
                else:
                    strip.setBrightness(0)
                    for i in range(30):
                        strip.setPixelColorRGB( i, 0, 0, 0)
                    strip.show()
                    time.sleep(0.5)
                    return
        except KeyboardInterrupt:
                strip._cleanup()
                strip.setBrightness(0)
                for i in range(30):
                    strip.setPixelColorRGB( i, 0, 0, 0)
                strip.show()
                time.sleep(0.5)
                return

    def sunlight(self):
        strip=self.strip
        self.interrupt=False
        try:
            brightness=strip.getBrightness()
            while not self.interrupt:
                strip.setBrightness(brightness)
#                brightness=strip.getBrightness()
                if brightness<255:
                    brightness = brightness + 1
##                    print(brightness)
                    for i in range(30):
                        strip.setPixelColorRGB( i, 171, 227, 81)
                        i=i+1
                    strip.show()
                    time.sleep(0.0001)
                else:
                    return
                    strip.setBrightness(0)
                    for i in range(30):
                        strip.setPixelColorRGB( i, 0, 0, 0)
                    strip.show()
                    time.sleep(0.5)
                    return
        except KeyboardInterrupt:
                strip._cleanup()
                strip.setBrightness(0)
                for i in range(30):
                    strip.setPixelColorRGB( i, 0, 0, 0)
                strip.show()
                time.sleep(0.5)
                return
#
#    def colorWipe(self,strip,color,wait_ms=50):
#        """Wipe color across display a pixel at a time."""
#        for i in range(strip.numPixels()):
#            strip.setPixelColor(i, color)
#            strip.show()
#            time.sleep(wait_ms/1000.0)



        

    
if __name__=="__main__":
    C=Curtain()
    C.DOWN()
