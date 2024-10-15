from pypylon import pylon
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import datetime

""" Define class for storing/displaying 3 triggered images, 
using image sequence to calculate corrected image,
then saving the resulting image as .txt file for analysis
Requires pypylon
"""
# Helpers

def fix_hot_pixels(image, type='simple'):
        with open('./hotpixels.npy', 'rb') as f:
            hot_pixels = np.load(f)
        
        rows = hot_pixels[:,0]
        cols = hot_pixels[:,1]

        if type == 'simple':
            # removal
            image[rows, cols] = 0 # can be adjusted to be more elaborate...
            return image
        else: # use inpainting
            mask = np.zeros(image.shape, dtype=np.uint8)
            mask[rows, cols] = 1
            fixed = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

            return fixed

class TriggeredSequence:
    def __init__(self, save_path='Basler', autosave=False, smoothing='Gaussian'):
        self.images = {}
        self.image_count = 0
        self.image_types = ['shadow', 'light', 'dark']
        self.save_path = save_path
        self.autosave = autosave
        self.sequence_count = 0
        self.smoothing_type = smoothing


    def add_image(self, image):
        print("Img grabbed")
        self.images[self.image_types[self.image_count]] = image
        self.image_count += 1
        
        if self.image_count == 3:
            self.sequence_complete()
            self.image_count = 0
    

    def sequence_complete(self):
        self.sequence_count += 1
        print(f"Sequence {self.sequence_count} completed...")
        

    def calc_result(self):
        shadow = self.images['shadow']
        light = self.images['light']
        dark = self.images['dark']

        ### TESTING HOT PIXEL FIX
        # add some fake hot pixels
        
        light = fix_hot_pixels(light, type='simple')
        # cv2.imshow('fix', light)

        ### TESTING/IN PROGRESS - smoothing dark frame (and light frame)
        # dark = (dark + np.random.normal(0, 1530, dark.shape)).astype(np.uint16) # FOR TESTING add some noise
        if self.smoothing_type == 'Gaussian':
            dark = cv2.GaussianBlur(dark, (11, 11), 180)
            light = cv2.GaussianBlur(light, (11, 11), 180) # testing light frame smoothing
        
        elif self.smoothing_type == 'Median Blur':
            dark = cv2.medianBlur(dark.astype(np.uint8), 11) # lossy convert to 8bit
            light = cv2.medianBlur(light.astype(np.uint8), 11)
        
        # cv2.imshow('Smooth test', dark) # FOR TESTING/DISPLAY blur outcome (not needed in final code)

        shadow = np.maximum(shadow, dark)
        light = np.maximum(light, dark)

        # Absorption calculation
        result = np.where(
             (shadow <= dark) | ((light - dark) < (shadow - dark)), 1,
             np.round(1000.0 * np.log((light - dark) / (shadow - dark))).astype(np.uint16)
        )
        # handle NaN values
        result = np.nan_to_num(result, nan=0, posinf=0, neginf=0).astype(np.uint16) # posinf -> 65535??
        self.images['calc'] = result

    
    def save_result(self):
        """ Saves calculated absorption image in specified format for
        image analysis with viewing software on lab computer
        """
        data = self.images['calc']
        timestamp = datetime.datetime.now().strftime('%m%d') # MMDD
        # Make dir if necessary
        if not os.path.exists(f"{self.save_path}/{timestamp}"):
            os.makedirs(f"{self.save_path}/{timestamp}")
        ## Edit filename convention here ## 
        base_name = f"{self.save_path}/{timestamp}/b{timestamp}"
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
        

    def display_calculated_image(self):
        """ Uses matplotlib window to display result image with colormap...
        needs to be adjusted to better integrate with tkinter interface
        Moving plt window (in software mode) will crash python...doesn't seem to happen
        when using hardware trigger (on lab computer at least)
        """
        self.calc_result()
        if self.autosave:
            self.save_result()
        img = self.images['calc']
        plt.imshow(img, cmap='viridis', vmax=np.max(img), vmin=np.min(img))
        plt.axis('off')
        plt.title('Calculated Image from Sequence')
        plt.tight_layout()
        plt.pause(0.1)
        plt.draw()


    # def display_images(self): # MESSY, not working currently
    #     plt.close('all')
    #     fig = plt.figure(figsize=(10,5))
    #     ax_shadow = plt.subplot(231)
    #     ax_light = plt.subplot(232)
    #     ax_dark = plt.subplot(233)
    #     ax_calc = plt.subplot(212)

    #     axs = [ax_shadow, ax_light, ax_dark, ax_calc]
    #     for i, (k, v) in enumerate(self.images.items()):
    #         axs[i].imshow(v, cmap='viridis', vmax=np.max(v), vmin=np.min(v))
    #         axs[i].set_title(k)
    #         axs[i].set_axis_off()

    #     # plt.pause(0.1) # plt.pause so non-blocking
    #     plt.tight_layout()
    #     plt.show()