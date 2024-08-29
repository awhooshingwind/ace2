import pypylon.pylon as py
import numpy as np
import cv2
import matplotlib.pyplot as plt

# handle exception trace for debugging 
# background loop
import traceback
import time


cam = py.InstantCamera(py.TlFactory.GetInstance().CreateFirstDevice())
cam.Open()

# to get consistant results it is always good to start from "power-on" state
cam.UserSetSelector.Value = "Default"
cam.UserSetLoad.Execute()

# cam.ExposureTime.Value = cam.ExposureTime.Min
cam.ExposureTime.Value = 10000 # 10 ms
cam.PixelFormat.Value = "Mono12p"

# show expected framerate max framerate ( @ minimum exposure time)
print(cam.ResultingFrameRate.Value)

# this results in frame period in µs
print(1 / cam.ResultingFrameRate.Value * 1e6)

# test images
numberOfImagesToGrab = 3
images = {}
img_names = ['shallow', 'light', 'dark']

cam.StartGrabbingMax(numberOfImagesToGrab)

while cam.IsGrabbing():
    for i in range(numberOfImagesToGrab):
        with cam.RetrieveResult(1000) as grab:
                tmp = grab.GetArray()
                # print(tmp.shape)
                images[img_names[i]] = tmp

cam.Close()

# calc test
def adjusted_image(images):
     shallow = images['shallow']
     light = images['light']
     dark = images['dark']
     
     #for testing with consecutive images
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
     return result

images['adjusted'] = adjusted_image(images)



for i, (k, v) in enumerate(images.items()):
    plt.figure(figsize=(10,5))
    plt.imshow(v, cmap='gray')
    plt.title(k)
    plt.axis('off')

plt.show()

