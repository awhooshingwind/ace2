"""Defines TriggeredSequence class for storing/displaying 3 triggered images for absorption imaging.

Current implementation is overloaded to also handle absorption calculation,
incoming image streaming and matplotlib display, hot pixel correction,
and saving images in appropriate .txt format for analysis...


"""

import datetime
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np

# Helpers
def fix_hot_pixels(image, test=False):
        if test:
            return image
        with open('./hotpixels.npy', 'rb') as f:
            hot_pixels = np.load(f)
        # print(hot_pixels.shape)
        rows = hot_pixels[:,0]
        cols = hot_pixels[:,1]
        # flag as negative value (-4000)
        image = image.astype(np.int16)
        image[rows, cols] = -4000 
        return image

def get_next_filenumber(save_path, prefix='b'):
    timestamp = datetime.datetime.now().strftime('%m%d') # MMDD
    # Make dir if necessary
    dir_path = Path(save_path)/timestamp
    dir_path.mkdir(exist_ok=True)
    max_number = 0
    pattern = f'{prefix}{timestamp}*.txt'
    for existing_file in dir_path.glob(pattern):
        try:
            fnum = existing_file.stem[len(f'{prefix}{timestamp}'):]
            if fnum.isdigit():
                max_number = max(max_number, int(fnum))
        except:
            continue
    return dir_path / f'{prefix}{timestamp}{max_number+1}.txt'

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
        # For matplotlib image display
        self.fig, self.ax = plt.subplots(figsize=(9,7.5))
        self.im = self.ax.imshow(np.ones((10,10)), cmap='viridis')
        self.ax.axis('off')
        self.ax.set_title('Waiting for image...')
        self.fig.tight_layout()
        
    def add_image(self, image):
        if self.singlet_flag == False:
            print("Img sequenced")
            self.images[self.image_types[self.image_count]] = image
            self.image_count += 1
            self.display_incoming(image)
            if self.image_count == 3:
                self.sequence_complete()
                self.image_count = 0

        if self.singlet_flag:
            self.images['calc'] = fix_hot_pixels(image)
            self.display_calculated_image(image)
            self.image_count += 1
            print(f"Single image #{self.image_count} grabbed....")
            self.display_incoming(image)
            self.sequence_count += 1
            self.resized_imgs = []
            if self.autosave:
                self.save_result()

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

    def sequence_complete(self):
        self.sequence_count += 1
        print(f"Sequence {self.sequence_count} completed...")
        self.calc_result()
        self.display_calculated_image(self.images['calc'])
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
        result = fix_hot_pixels(result) 
        self.images['calc'] = result
        if self.autosave:
            self.save_result(result)

    def save_result(self, data=None):
        """ Saves calculated absorption image in specified format for
        image analysis with viewing software on lab computer
        """
        if data is None:
            data = self.images['calc']
        # data = fix_hot_pixels(data) # or remove this
        filename = get_next_filenumber(self.save_path)
        h,w = data.shape
        header = (f"resx 1 widthx {w} centerx {w//2} resy 1 widthy {h} centery {h//2}")
        output_data = np.zeros((h+1,w+1),dtype=np.uint16)
        output_data[0,:] = np.arange(w+1)
        output_data[:,0] = np.arange(h+1)
        output_data[1:,1:] = data
        np.savetxt(filename, output_data, delimiter='\t', fmt='%d', header=header, comments='')
        print(f"{filename} saved")    

    def display_calculated_image(self, img):
        """ Uses matplotlib window to display result image with colormap...
        needs to be adjusted to better integrate with tkinter interface
        Moving plt window (in software mode) will crash python...doesn't seem to happen
        when using hardware trigger (on lab computer at least)
        """
        self.im.set_data(img)
        self.im.autoscale()
        self.fig.canvas.draw()
        self.ax.set_title(f'Triggered Image/Sequence #{self.sequence_count}')
        plt.pause(0.1)
        
