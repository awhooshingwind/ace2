import numpy as np
import os
import cv2
import imaging.camera_config as cc
from pypylon import pylon


""" From a dark frame, determine locations of 'hot pixels' and save coordinates. From those coordinates, generate a mask to correct for hot pixels in subsequent frames (or use Basler built-in pixel defect correction...)
"""

def take_dark_frame():
    cam = cc.init_camera()
    cam.Open()
    cam.PixelFormat.Value = "Mono12p"
    cam.Gain.Value = 48.0 # Max Gain
    cam.ExposureTime.Value = 10000000 # max exposure (10s)

    cam.StartGrabbingMax(1)
    try:
        
        while cam.IsGrabbing():
            # for exposure in exposure_times:
            # for i in range(num_frames)
                # camera.ExposureTime.Value = exposure
                
                # use the context handler, so you dont have to call "grabResult.Release" at the end
            with cam.RetrieveResult(int(10000000+1000), pylon.TimeoutHandling_ThrowException) as grabResult:
                if grabResult.GrabSucceeded():
                        
                    # Accessing image data
                    img = grabResult.GetArray()
                    print(f"img grabbed")
                        
    except Exception as e:
        print(f"Error {e}")   
         
    cam.StopGrabbing()
    cam.Close()
    return img

def find_hot_pixel(image, save=True):
    max = 4095 # 12bit
    # print(np.max(image))
    hot_pixels = image == max
    hot_pixel_coords = np.column_stack(np.where(hot_pixels))
    print(hot_pixel_coords.shape)

    if save:
        with open('hotpixels.npy', 'wb') as f:
            np.save(f, hot_pixel_coords)      

    return hot_pixel_coords
    


def hot_button():
      dark = take_dark_frame()
      find_hot_pixel(dark)
      print('hot pixel routine')
'''
## TESTING
# Compare dark frames taken with different gain values (max at 40, max analog at 23)
with open('./noise/b10101.npy', 'rb') as f:
    dark_frame = np.load(f)
    hot40 = find_hot_pixel(dark_frame, save=True)

with open('./noise/b10101_23gain.npy', 'rb') as f:
    dark_frame_23 = np.load(f)
    hot23 = find_hot_pixel(dark_frame_23)

# Find the common hot pixels for sanity check
common_hot_pixels = np.intersect1d(hot40.view([('', hot40.dtype)] * hot40.shape[1]),
                                   hot23.view([('', hot23.dtype)] * hot23.shape[1]))

# Convert the result back to regular coordinates
common_hot_pixels = common_hot_pixels.view(hot40.dtype).reshape(-1, 2)
# print(np.equal(common_hot_pixels, hot23))
# print(common_hot_pixels.shape)

'''



