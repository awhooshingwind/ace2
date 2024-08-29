import pypylon.pylon as py
import pypylon.genicam as geni
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os

import time
import datetime
import queue

# Define class for storing 3 images and doing img calc
class TriggeredSequence:
    def __init__(self, save_path='Basler', autosave=False):
        self.images = {}
        self.image_count = 0
        self.image_types = ['shallow', 'light', 'dark']
        self.save_path = save_path
        self.autosave = autosave
        self.sequence_count = 1

    def add_image(self, image):
        self.images[self.image_types[self.image_count]] = image
        self.image_count += 1
        if self.image_count == 3:
            self.sequence_complete()
            self.image_count = 0
    
    def sequence_complete(self):
        self.calc_result()
        if not self.autosave:
            self.save_result()
        self.display_images()
        self.sequence_count += 1

    def calc_result(self):
        shallow = self.images['shallow']
        light = self.images['light']
        dark = self.images['dark']
        # for testing with consecutive images
        # small eps to prevent problem values in calc
        eps = 1e-5
        shallow = np.maximum(shallow, dark + eps)
        light = np.maximum(light, dark + eps)
        result = np.where(
             (shallow <= dark) | ((light - dark) < (shallow - dark)), 1,
             np.round(1000.0 * np.log((light - dark) / (shallow - dark))).astype(np.uint16)
        )
        
        # handle NaN values for testing
        result = np.nan_to_num(result, nan=0, posinf=0, neginf=0).astype(np.uint16)
        
        if self.autosave:
            self.save_result(result)
        
        self.images['calc'] = result
    
    def save_result(self):
        data = self.images['calc']
        # Make dir if necessary
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        ## Edit filename convention here ## 
        timestamp = datetime.datetime.now().strftime('%m%d')
        # as is - overwrites existing images each session for testing
        base_name = f"{self.save_path}/b{timestamp}{self.sequence_count}"
        # save as .tif
        # cv2.imwrite(base_name+'.tif', data)
        # save as .txt (in specified format)
        h,w = data.shape
        header = (f"resx 1 widthx {w} centerx {w//2} "
                  f"resy 1 widthy {h} centery {h//2}\n")
        # make second row of col indices
        col_inds = "\t".join(map(str, range(w))) + "\n"
        # Write txt file
        fname = base_name + '.txt'
        # check for duplicates, add _{n} if exists
        dup_count = 1
        while os.path.exists(fname):
            fname = f"{base_name}_{dup_count}.txt"
            dup_count += 1
        # write txt file
        with open(fname, 'w') as f:
            f.write(header)
            f.write(col_inds)
            for i, row in enumerate(data):
                row_data = "\t".join(map(str, row))
                f.write(f"{i+1}\t+{row_data}\n")


    def display_images(self):
        plt.close('all')
        for i, (k, v) in enumerate(self.images.items()):
            plt.figure(figsize=(10,5))
            plt.imshow(v, cmap='viridis')
            # print(v.shape)
            plt.clim(vmin=np.min(v), vmax=np.max(v))
            plt.title(k)
            plt.axis('off')
            plt.colorbar()
        plt.pause(0.001) # plt.pause so non-blocking
        plt.draw()
        # plt.show()


# open the camera
tlf = py.TlFactory.GetInstance()
cam = py.InstantCamera(tlf.CreateFirstDevice())
cam.Open()

# get clean powerup state
cam.UserSetSelector.Value = "Default"
cam.UserSetLoad.Execute()

# Hardware Trigger Config
# setup the io section
# cam.LineSelector.Value = "Line1"
# cam.LineMode.Value = "Input"

# # setup the trigger / acquisition controls

cam.TriggerSelector.Value = "FrameStart"
# cam.TriggerSource.Value = "Line1"
cam.TriggerMode.Value = "On"
# print(cam.TriggerActivation.Value)

# Software trigger config (for testing)
cam.TriggerSource.Value = "Software"

# definition of event handler class 
class TriggeredImage(py.ImageEventHandler):
    def __init__(self, img_queue):
        super().__init__()
        self.image_queue = img_queue
    
    def OnImageGrabbed(self, camera, grabResult):
        if grabResult.GrabSucceeded():
            img = grabResult.GetArray()
            self.image_queue.put(img)
    
# create classes
image_queue = queue.Queue()
image_handler = TriggeredImage(image_queue)
trigger_sequence = TriggeredSequence()

# register handler
# remove all other handlers
cam.RegisterImageEventHandler(image_handler, 
                              py.RegistrationMode_Append, 
                              py.Cleanup_None)

def getkey():
    return input("Enter \"t\" to trigger the camera or \"e\" to exit and press enter? (t/e) ")

try:
    # start grabbing with background loop (hardware trigger)
    cam.StartGrabbingMax(100, py.GrabStrategy_LatestImages, py.GrabLoop_ProvidedByInstantCamera)
    # Start the grabbing using the grab loop thread, by setting the grabLoopType parameter
    # to GrabLoop_ProvidedByInstantCamera. The grab results are delivered to the image event handlers.
    # The GrabStrategy_OneByOne default grab strategy is used.
    # cam.StartGrabbing(py.GrabStrategy_OneByOne, py.GrabLoop_ProvidedByInstantCamera)

    while True:
    # wait ... or do something relevant
        time.sleep(0.05)
        # Process Images
        if not image_queue.empty():
            img = image_queue.get()
            trigger_sequence.add_image(img)
        key = getkey()
        # print(key)
        if key.lower() == 't':
            # Execute the software trigger. Wait up to 100 ms for the camera to be ready for trigger.
            if cam.WaitForFrameTriggerReady(100, py.TimeoutHandling_ThrowException):
                cam.ExecuteSoftwareTrigger()
        if key.lower() == 'e':
            break

    # stop grabbing
    cam.StopGrabbing()

except geni.GenericException as e:
        # Error handling.
        print("An exception occurred.", e)

cam.Close()
