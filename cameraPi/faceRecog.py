import picamera
import os
import requests

class FaceRecog():
    def __init__(self,camera=None):
        if camera is None:
            self.camera=picamera.PiCamera()
        else:
            self.camera=camera
        self.camera.rotation=180
            
    def compare(self,name,source='temp.jpg'):
        url='https://api-cn.faceplusplus.com/facepp/v3/compare'
        target='faceDB/'+name+'.jpg'
        data={
            'api_key':'LCbKSGF2roARhyhj_8NuZ-cMXbTba2kQ',
            'api_secret':'VCZ3AIFMxFEgr-TIAA7OYAHwfdNtd7ex'
            }
        files={
            'image_file1':open(source,'rb'),
            'image_file2':open(target,'rb')
            }
        res=requests.post(url,data=data,files=files)
        res=res.json()
        print(res)
        if 'thresholds' in res.keys():
            thresholds=res['thresholds']
            confidence=res['confidence']
            thre_3=thresholds['1e-3']
            thre_4=thresholds['1e-4']
            thre_5=thresholds['1e-5']
            if confidence > thre_5:
                return 3
            elif confidence>thre_4:
                return 2
            elif confidence>thre_3:
                return 1
            else:
                return 0
        else:
            return -1
            
    def checkFace(self):
        self.camera.capture('temp.jpg')
        global checkRes
        checkRes=[]
        dirc=os.path.join(os.getcwd(),"faceDB")
        for root,dirs,files in os.walk(dirc):
            for file in files:
                if file.endswith('jpg'):
                    name=file.replace('.jpg','')
                    res=self.compare(name)
#                    res=0
                    if res==-1:
                        print("no face!")
                        return
                    else:
                        checkRes.append((name,res))
                        
        checkRes.sort(key=lambda:x:x[1])
        name,conf=checkRes[-1]
        if conf==0:
            return False
        else:
            return name
        
        
f=FaceRecog()
f.checkFace()