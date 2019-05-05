from util import *
import _thread as thread
import atexit

"""Parameters"""
TEMP="Temp"
HUMD="Humd"
PRES="Pres"
"""----------"""
GPIO.setmode(GPIO.BCM)


    
    
class controllerPi(Client):
    def __init__(self,server_ip,port=12345):
        super().__init__(server_ip,port)
        
        self.tar_temp=31
        self.tar_humd=60
        self.tol_temp=0.2
        self.tol_humd=0.5
        
        self.IP=server_ip
        self.fanSet=FanSet()
        self.heater=Heater()
        self.humidifier=Humidifier()
        self.water=Water()
        self.buzzer=Buzzer()
        self.curtain=Curtain()
        self.bluetooth=Bluetooth()
        self.led=LED()
        
        self.setTemp()
        self.setHumd()
        self.setWaterTime()

        self.humdStatus=False
        

    def setTemp(self,tolerance=2):
        targetTemp=int(input("Target Temp:"))
        self.tar_temp=targetTemp
        self.tol_temp=tolerance

    def setHumd(self,tolerance=2):
        targetHumd=int(input("Target Humidity:"))
        self.tar_humd=targetHumd
        self.tol_humd=tolerance

    def setWaterTime(self,):
        duration=int(input("Target watering Duration"))
        startTime=int(input("Watering start time"))
        self.water_time=startTime
        self.water_duration=duration
        
    def run(self):
#        self.handleTemp()
        
        thread.start_new_thread(self.senseAndHandle,())
        thread.start_new_thread(self.handleWater,())
        thread.start_new_thread(self.faceRecognition,())
        thread.start_new_thread(self.handleLight,())
        thread.start_new_thread(self.voiceControl,())
        while True:
            donothing=0
        print("end")

    def senseAndHandle(self):
        while True:
            self.handleTemp()
            self.handleHumd()
            time.sleep(1)
        

    def handleTemp(self):    
        temp=self.senseData('Temp')
        if temp==None: return 
        print("Temp",temp)
        if temp>self.tar_temp+self.tol_temp:
            self.fanSet.turnAllON()
            self.heater.switch(False)
        elif temp<self.tar_temp-self.tol_temp:
            self.fanSet.turnAllOFF()
            self.heater.switch(True)
            
    
    def handleHumd(self):
        temp=self.senseData('Humd')
        if temp==None: return 
        print("Humd",temp)
        if temp<self.tar_humd-self.tol_humd and self.humdStatus==False:
##            print("ON")
            self.humidifier.switch()
            self.humdStatus=True
        elif temp>self.tar_humd+self.tol_humd and self.humdStatus==True:
##            print("OFF")
            self.humidifier.switch()
            self.humdStatus=False

    def handleWater(self):
##        curTime=time.gmtime(t)
##        hour=(curTime.tm_hour+8)%24
##        mint=curTime.tm_min
##        if(hour==7 and mint==0):
##            self.water.turnON()
##            time.sleep(self.water_duration)
##            self.water.turnOFF()
        hour=0
        hourTime=time.time()
        startTime=None
        while True:
            curTime=time.time()
            hour=int((curTime-hourTime)/5)%24
            if hour==self.water_time:
                self.water.switch(True)
                startTime=time.time()
            if startTime is not None and curTime-startTime>self.water_duration:
##                print("end water")
                self.water.switch(False)
                startTime=None
            time.sleep(1)
        
    def handleLight(self):
##        curTime=time.gmtime(t)
##        hour=(curTime.tm_hour+8)%24
##        mint=curTime.tm_min
##        if(hour==7 and mint==0):
##            self.led.switchMode('sunlight')
##            self.curtain.UP()
##        elif(hour==19 and mint==0):
##            self.led.switchMode('bedtime')
##            self.curtain.DOWN()
        hour=0
        while True:
            hour=(hour+1)%24
            print("hour:",hour)
            if hour==3:
                self.curtain.switchMode('UP')
                self.led.switchMode('sunlight')                
            elif hour==6:
                self.curtain.switchMode('DOWN')
                self.led.switchMode('bedtime')                
            time.sleep(5)

    def voiceControl(self):
        while True:
            cmd=self.bluetooth.readword()
            if cmd=="light on":
                self.led.switchMode('ON')
            elif cmd=="light off":
                self.led.switchMode('OFF')
            elif cmd.split(' ')[0]=="temp":
                tar_temp=int(cmd.split(' ')[1])
                self.tar_temp=tar_temp
                thread.start_new_thread(self.buzzer.ring())
        
    def senseData(self,dataType):
        #dataType: Temp|Humd|Pres
##        print("sense "+dataType)
        self.sendMsg("sense "+dataType)
        res=self.receiveMsg()
        try:
            res=float(res)
        except:
            return None
        return res
    
    def startCamera(self,port=12346):
        self.camera=CameraServer(self.IP,port)
        self.sendMsg("camera start")
        self.camera.waitConnection()
        
    def closeCamera(self):
        if self.camera:
            self.sendMsg("camera close")
            self.camera.end()
    
    def disconnect(self):
        self.sendMsg("END")
        self.server.close()

    def faceRecognition(self):
        pass
##        GPIO.setup(9,GPIO.IN, GPIO.PUD_UP)
##        while True:
##            if (GPIO.input(9)==False):
##                self.sendMsg("camera check")
##                res=self.receiveMsg().split(' ')
##                name,confidence=res[0],res[1]
##                if confidence<70%:
##                    for i in range(3):
##                        self.buzzer.ring()
##                else:
##                    print("Welcome back,",name)
                   
                    

if __name__=="__main__":
    global s
    s=controllerPi('172.20.10.10',12346)
    def cleanup():
        global s
        s.sendMsg("END")
    
    atexit.register(cleanup)
    s.run()
    t=1
