import matplotlib.pyplot as plt
import numpy as np
import os
import datetime

""" Define class for storing/displaying 3 triggered images, 
using image sequence to calculate corrected image,
then saving the resulting image as .txt file for analysis
Requires pypylon
"""
class TriggeredSequence:
    def __init__(self, save_path='Basler', autosave=False):
        self.images = {}
        self.image_count = 0
        self.image_types = ['shadow', 'light', 'dark']
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
        # if self.autosave:
        #     self.save_result()
        # self.display_images()
        # self.display_calculated_image()
        self.sequence_count += 1


    def calc_result(self):
        shadow = self.images['shadow']
        light = self.images['light']
        dark = self.images['dark']
        # for testing with consecutive images
        # small eps to prevent problem values in calc
        eps = 1e-5
        shadow = np.maximum(shadow, dark + eps)
        light = np.maximum(light, dark + eps)
        result = np.where(
             (shadow <= dark) | ((light - dark) < (shadow - dark)), 1,
             np.round(1000.0 * np.log((light - dark) / (shadow - dark))).astype(np.uint16)
        )
        # handle NaN values for testing
        result = np.nan_to_num(result, nan=0, posinf=0, neginf=0).astype(np.uint16)
        self.images['calc'] = result
        if self.autosave:
            self.save_result()


    def save_result(self):
        data = self.images['calc']
        # Make dir if necessary
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        ## Edit filename convention here ## 
        timestamp = datetime.datetime.now().strftime('%m%d')
        base_name = f"{self.save_path}/b{timestamp}{self.sequence_count}"
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

    def display_calculated_image(self):
        img = self.images['calc']
        # plt.ion()
        plt.imshow(img, cmap='viridis', vmax=np.max(img), vmin=np.min(img))
        plt.axis('off')
        plt.title('Calculated Image from Sequence')
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)
        plt.show(block=False)

    def display_images(self):
        plt.ion()
        ax_shadow = plt.subplot(231)
        ax_light = plt.subplot(232)
        ax_dark = plt.subplot(233)
        ax_calc = plt.subplot(212)

        axs = [ax_shadow, ax_light, ax_dark, ax_calc]
        for i, (k, v) in enumerate(self.images.items()):
            axs[i].imshow(v, cmap='viridis', vmax=np.max(v), vmin=np.min(v))
            axs[i].set_title(k)
            axs[i].set_axis_off()
        plt.tight_layout()
        plt.draw()
        plt.pause(0.1) # plt.pause so non-blocking
        
        