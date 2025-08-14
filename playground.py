from pypylon import pylon
import cv2
import numpy as np
import time
from imaging import config_camera as cc
import trig_seq as ts

class ImageHandler(pylon.ImageEventHandler):
    def __init__(self, image_queue):
        super().__init__()
        self.image_queue = image_queue
        self.image_count = 0
        self.img_list = []

    def OnImageGrabbed(self, camera, grabResult):
        try:
            if grabResult.GrabSucceeded():
                self.image_count += 1
                print(f'Grabbed {self.image_count}')
                img = grabResult.Array
                img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)
                self.image_queue.put(img)  # Add image to queue
                self.img_list.append(img)
            else:
                raise RuntimeError("Grab failed")
        except Exception as e:
            print(e)


