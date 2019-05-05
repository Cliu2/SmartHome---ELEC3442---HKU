from util import *

class sensorPi(Server):
    def __init__(self, port=12345):
        super().__init__(port)
        self.hat=senseHat()
        self.run()
        
    def run(self):
        while True:
            cmd=self.receiveMsg()
            print("d")
            print(cmd)
            cmdType=cmd[0]      #(sense <sensor>) or (camera <action> [<ip> <port>])
            if cmdType=="sense":
                self.sense(cmd[1])
            elif cmdType=="camera":
                action=cmd[1]
                if action=="start":
                    self.startCamera(cmd[2],cmd[3])
                elif action=="close":
                    self.closeCamera()
            elif cmdType=="END":
                print("connection end")
                self.con.close()
                self.waitConnection()
                
    def sense(self,sensor):
        print("sense")
        if sensor=="Temp":
            temp=self.hat.getTemp()
            self.sendMsg(temp)
        elif sensor=="Humd":
            humd=self.hat.getHumid()
            self.sendMsg(humd)
        elif sensor=="Pres":
            pres=self.hat.getPres()
            self.sendMsg(pres)
            
    def startCamera(self,ip,port):
        port=int(port)
        self.camera=CameraClient(ip,port)
        
    def closeCamera(self):
        if self.camera:
            self.camera.end()
            
s=sensorPi(12346)
s.run()
        