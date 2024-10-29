from pypylon import pylon
import cv2
import matplotlib.pyplot as plt
import numpy as np
import imaging.trig_seq as ts
import imaging.camera_config as cc
import time


class ImageHandler(pylon.ImageEventHandler):
    def __init__(self):
        super().__init__()
        self.image_list = []
        self.image_count = 0
    
    def OnImageGrabbed(self, camera, grabResult):
        try:
            # print('hmm')
            if grabResult.GrabSucceeded():
                self.image_count += 1
                print(f'grabbed {self.image_count}')
                img = grabResult.Array
                img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)
                self.image_list.append(img)
            else:
                raise RuntimeError("Grab failed")
        except Exception as e:
            print(e)

def test_images():
    cam = cc.emu_camera()

    print(cam.GetDeviceInfo().GetModelName())

    handler = ImageHandler()

    try:
        cam.RegisterImageEventHandler(handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly, pylon.GrabLoop_ProvidedByInstantCamera)

        for _ in range(9):
            time.sleep(0.1)
            if cam.WaitForFrameTriggerReady(1000, pylon.TimeoutHandling_ThrowException):
                cam.ExecuteSoftwareTrigger()
                print('trigger')
                time.sleep(0.2)
    except Exception as e:
        print(e)
        
    finally:
        cam.StopGrabbing()
        cam.DeregisterImageEventHandler(handler)
        cam.Close()  # Ensure the camera is properly closed

    return handler.image_list

def button_wrap():
    test = ts.TriggeredSequence()
    for img in test_images():
        test.add_image(img)


    

    
        
    
    
