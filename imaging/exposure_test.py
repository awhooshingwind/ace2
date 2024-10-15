# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 15:22:53 2024

Basler ace2 camera characterization. Take consecutive 'dark' frames
incrementing exposure time, saving resulting images for analysis.

From product page: min exposure = 19 us, max = 10000000 us

@author: Experiment
"""

from pypylon import pylon
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime

num_frames = 10
# min_exposure = 10000000
max_exposure = 10000000
# max_exposure = 10000000

mean_vals = []
camera_gain = 40.0

images = []

# exposure_times = np.linspace(min_exposure, max_exposure, num_frames)
# exposure_times=[min_exposure, max_exposure]

def cv2_save_img(image):
    data = image
    save_path='noise'
    timestamp = datetime.datetime.now().strftime('%m%d') # MMDD
    # Make dir if necessary
    if not os.path.exists(f"{save_path}/{timestamp}"):
        os.makedirs(f"{save_path}/{timestamp}")
    ## Edit filename convention here ## 
    base_name = f"{save_path}/{timestamp}/b{timestamp}"
    filenumber = 1
    fname = base_name + str(filenumber) + '.tif'
    # check for duplicates, increment file number if exists
    while os.path.exists(fname):
        filenumber += 1
        fname = f"{base_name}{str(filenumber)}.tif"
    cv2.imwrite(fname, image)
    
    

def save_img(image):
    """ Saves calculated absorption image in specified format for
    image analysis with viewing software on lab computer
    """
    data = image
    save_path='Basler'
    timestamp = datetime.datetime.now().strftime('%m%d') # MMDD
    # Make dir if necessary
    if not os.path.exists(f"{save_path}/{timestamp}"):
        os.makedirs(f"{save_path}/{timestamp}")
    ## Edit filename convention here ## 
    base_name = f"{save_path}/{timestamp}/b{timestamp}"
    filenumber = 1
    fname = base_name + str(filenumber) + '.txt'
    # check for duplicates, increment file number if exists
    while os.path.exists(fname):
        filenumber += 1
        fname = f"{base_name}{str(filenumber)}.txt"
    # save as .txt (in specified format)
    h,w = data.shape
    header = (f"resx 1 widthx {w} centerx {w//2} "
              f"resy 1 widthy {h} centery {h//2}\n")
    # make second row of col indices
    col_inds = "\t".join(map(str, range(w))) + "\n"
    # write txt file
    with open(fname, 'w') as f:
        f.write(header)
        f.write(col_inds)
        for i, row in enumerate(data):
            row_data = "\t".join(map(str, row))
            f.write(f"{i+1}\t+{row_data}\n")
    print(f"{fname} saved")

def init_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    try:
        # Set camera parameters f
        camera.Open()
        # to get consistant results it is always good to start from "power-on" state
        camera.UserSetSelector.Value = "Default"
        camera.UserSetLoad.Execute()
        
        camera.PixelFormat.Value = "Mono12p"
        camera.Gain.Value = camera_gain

    except Exception as e:
        print(f"Error when configuring the camera: {e}")
    
    return camera

camera = init_camera()
camera.ExposureTime.Value = max_exposure


def grab_frames():
    n = 0
    
    camera.StartGrabbingMax(num_frames)
    try:
        
        while camera.IsGrabbing():
            # for exposure in exposure_times:
            # for i in range(num_frames)
                # camera.ExposureTime.Value = exposure
                
                # use the context handler, so you dont have to call "grabResult.Release" at the end
            with camera.RetrieveResult(int(max_exposure+1000), pylon.TimeoutHandling_ThrowException) as grabResult:
                if grabResult.GrabSucceeded():
                        
                    # Accessing image data
                    img = grabResult.GetArray()
                    print(f"img grabbed")
                    # print(np.max(img))
                    # img_mean = np.mean(img)
                    # mean_vals.append(img_mean)
                    # images[n] = img
                    images.append(img)
                    n+=1
            if n == 2:
                # camera.StopGrabbing()
                break
                        
    except Exception as e:
        print(f"Error {e}")   
         
    camera.StopGrabbing()
    camera.Close()

grab_frames()

img1 = images[0]
img2 = images[1]

subtracted = img2.astype(np.int16)-img1.astype(np.int16)

stats = subtracted

# print(img2-img1)

# save_img(images[max_exposure])
# for image in images:
#     cv2_save_img(image)

mean_vals = np.where(stats < 4090, stats, 0)
img_mean = np.mean(img2)
std_dev = np.std(stats)

# print(f'mean: {np.mean(mean_vals)}')
print(img_mean)
print(f'std: {std_dev}')

with open('noise/stats.txt', 'a') as f:
    f.write(f'{max_exposure}\t{img_mean}\t{std_dev}\n')
    

counts, bins = np.histogram(stats, bins=100, range=(-5000, 5000))
plt.stairs(counts, bins)

# plt.hist(long_exp)

# plt.scatter(exposure_times/1000, mean_vals)
# plt.xlabel('Exposure Time [ms]')
# plt.ylabel('Dark Frame Mean')
# plt.title(f'{num_frames} Dark Frames with Increasing Exposure Times, Gain at {camera_gain} dB')
plt.grid()
plt.show()