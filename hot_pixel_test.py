import numpy as np
import os
import cv2

# import matplotlib.pyplot as plt


""" From a dark frame, determine locations of 'hot pixels' and save coordinates. From those coordinates, generate a mask to correct for hot pixels in subsequent frames (or use Basler built-in pixel defect correction...)
"""

def find_hot_pixel(image, save=False):
    max = 4095 # 12bit
    # print(np.max(image))
    hot_pixels = image == max
    hot_pixel_coords = np.column_stack(np.where(hot_pixels))
    print(hot_pixel_coords.shape)

    if save:
        with open('hotpixels.npy', 'wb') as f:
            np.save(f, hot_pixel_coords)      

    return hot_pixel_coords
    

frame_list = os.listdir('noise')
# print(frame_list)

with open('./noise/b10101.npy', 'rb') as f:
    dark_frame = np.load(f)
    hot40 = find_hot_pixel(dark_frame, save=True)

with open('./noise/b10101_23gain.npy', 'rb') as f:
    dark_frame_23 = np.load(f)
    hot23 = find_hot_pixel(dark_frame_23)

# Find the common hot pixels
common_hot_pixels = np.intersect1d(hot40.view([('', hot40.dtype)] * hot40.shape[1]),
                                   hot23.view([('', hot23.dtype)] * hot23.shape[1]))

# Convert the result back to regular coordinates
common_hot_pixels = common_hot_pixels.view(hot40.dtype).reshape(-1, 2)
# print(np.equal(common_hot_pixels, hot23))
# Print or use the coordinates as needed
# print(common_hot_pixels.shape)


## TESTING

# img_path = 'noise/0926'
# img_list = os.listdir(img_path)

# for i in range(len(img_list)):
#     tmp = cv2.imread(f'{img_path}/{img_list[i]}')
#     print(find_hot_pixel(tmp))

# Make 'test image' to simulate hot pixels
# h = 1200
# w = 1920

# # dark_frame = np.random.randint(65000, 65534, size=(h, w), dtype=np.uint16) # random noise image
# dark_frame = np.zeros((h,w))
# N_hot_pixels = 20300

# hot_pixel_indices = np.random.choice(h*w, N_hot_pixels, replace=False)
# hot_pixel_coords = np.unravel_index(hot_pixel_indices, (h,w))

