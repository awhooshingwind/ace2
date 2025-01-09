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
def fix_hot_pixels(image):
        with open('./hotpixels.npy', 'rb') as f:
            hot_pixels = np.load(f)
        # print(hot_pixels.shape)

        rows = hot_pixels[:,0]
        cols = hot_pixels[:,1]

        # flag as negative value (-4000)
        image = image.astype(np.int16)
        image[rows, cols] = -4000 
        return image


class TriggeredSequence:
    def __init__(self, save_path='Basler', autosave=False, smoothing='Gaussian', singlet_flag=False):
        self.images = {}
        self.image_count = 0
        self.image_types = ['shadow', 'light', 'dark']
        self.save_path = save_path
        self.autosave = autosave
        self.sequence_count = 0
        self.smoothing_type = smoothing
        self.singlet_flag = singlet_flag

        self.figh, self.figw = 300, 1200
        if singlet_flag:
            self.figw = 400
        self.combined_image = np.zeros((self.figh, self.figw), dtype=np.uint16)
        self.resized_imgs = []
        # cv2.imshow('Triggered_Images', self.combined_image) # testing for event handler
    
        
    def add_image(self, image):
        if not self.singlet_flag:
            print("Img sequenced")
            self.images[self.image_types[self.image_count]] = image
            self.image_count += 1
            self.display_incoming(image)
            if self.image_count == 3:
                self.sequence_complete()
                self.image_count = 0

        if self.singlet_flag:
            self.images['calc'] = fix_hot_pixels(image)
            self.display_incoming(image)
            self.image_count += 1
            self.single_complete()

    def display_incoming(self, image):
        # Display incoming images, testing for event handler approach
        w_ratio = self.figw
        if not self.singlet_flag:
            w_ratio = self.figw//3
    
        self.resized_imgs.append(image)
            
        for i in range(len(self.resized_imgs)):
            self.resized_imgs[i] = cv2.resize(self.resized_imgs[i], (w_ratio, self.figh))
            self.combined_image[0:self.figh, i*w_ratio:(i+1)*w_ratio] = self.resized_imgs[i]
            cv2.imshow('Triggered_Images', self.combined_image)
    
    def single_complete(self):
        print(f"Single image #{self.image_count} grabbed....")
        self.display_calculated_image()
        self.resized_imgs = []



    def sequence_complete(self):
        self.sequence_count += 1
        print(f"Sequence {self.sequence_count} completed...")
        self.calc_result()
        self.display_calculated_image()
        self.resized_imgs = []
        

    def calc_result(self):
        shadow = self.images['shadow']
        light = self.images['light']
        dark = self.images['dark']

        ### TESTING/IN PROGRESS - smoothing dark frame (and light frame)
        # dark = (dark + np.random.normal(0, 1530, dark.shape)).astype(np.uint16) # FOR TESTING add some noise
        if self.smoothing_type == 'Gaussian':
            dark = cv2.GaussianBlur(dark, (11, 11), 180)
            light = cv2.GaussianBlur(light, (11, 11), 180) # testing light frame smoothing
        
        elif self.smoothing_type == 'Median Blur':
            dark = cv2.medianBlur(dark.astype(np.uint8), 11) # lossy convert to 8bit
            light = cv2.medianBlur(light.astype(np.uint8), 11)
        

        shadow = np.maximum(shadow, dark)
        light = np.maximum(light, dark)

        # Absorption calculation
        result = np.where(
             (shadow <= dark) | ((light - dark) < (shadow - dark)), 1,
             np.round(1000.0 * np.log((light - dark) / (shadow - dark))).astype(np.uint16)
        )
        # handle NaN values
        result = np.nan_to_num(result, nan=0, posinf=0, neginf=0).astype(np.uint16) 
        result = fix_hot_pixels(result) # remove later
        self.images['calc'] = result

    
    def save_result(self):
        """ Saves calculated absorption image in specified format for
        image analysis with viewing software on lab computer
        """
        data = self.images['calc']
        # data = fix_hot_pixels(data) # or remove this
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
        if self.autosave:
            self.save_result()
        img = self.images['calc']
        plt.imshow(img, cmap='viridis', vmax=np.max(img), vmin=np.min(img))
        plt.axis('off')
        plt.title('Calculated Image from Sequence')
        plt.tight_layout()
        plt.draw()
        plt.pause(0.01)
        