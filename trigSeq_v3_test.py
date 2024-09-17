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

        # TESTING - smoothing dark frame
        dark = (dark + np.random.normal(0, 25530, dark.shape)).astype(np.uint16) # add some noise SOFTWARE

        if self.smoothing_type == 'Gaussian':
            dark = cv2.GaussianBlur(dark, (11, 11), 180)
        
        elif self.smoothing_type == 'Median Blur':
            dark = cv2.medianBlur(dark.astype(np.uint8), 11) # lossy convert to 8bit
        
        cv2.imshow('Dark test', dark) # FOR TESTING/DISPLAY blur outcome (not needed in final code)

        shadow = np.maximum(shadow, dark)
        light = np.maximum(light, dark)
        result = np.where(
             (shadow <= dark) | ((light - dark) < (shadow - dark)), 1,
             np.round(1000.0 * np.log((light - dark) / (shadow - dark))).astype(np.uint16)
        )
        # handle NaN values for testing
        result = np.nan_to_num(result, nan=0, posinf=0, neginf=0).astype(np.uint16)
        self.images['calc'] = result
        


    def save_result(self):
        data = self.images['calc']
        timestamp = datetime.datetime.now().strftime('%m%d')
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
        self.calc_result()
        if self.autosave:
            self.save_result()
        img = self.images['calc']
        # img = self.images['dark'] # !!! FOR TESTING DARK FRAME SMOOTHING !!!!
        plt.imshow(img, cmap='viridis', vmax=np.max(img), vmin=np.min(img))
        plt.axis('off')
        plt.title('Calculated Image from Sequence')
        plt.tight_layout()
        plt.pause(0.01)
        plt.draw()
        plt.show(block=False)


    def display_images(self):
        plt.close('all')
        fig = plt.figure(figsize=(10,5))
        ax_shadow = plt.subplot(231)
        ax_light = plt.subplot(232)
        ax_dark = plt.subplot(233)
        ax_calc = plt.subplot(212)

        axs = [ax_shadow, ax_light, ax_dark, ax_calc]
        for i, (k, v) in enumerate(self.images.items()):
            axs[i].imshow(v, cmap='viridis', vmax=np.max(v), vmin=np.min(v))
            axs[i].set_title(k)
            axs[i].set_axis_off()

        # plt.pause(0.1) # plt.pause so non-blocking
        plt.tight_layout()
        plt.show()

def config_camera(camera, EXTERNAL_TRIGGER):
    try:
        # setup camera aoi
        camera.Open()
        
        if EXTERNAL_TRIGGER:
            camera.TriggerSource.Value = "Line1"
            camera.PixelFormat.Value = "Mono12p"
            camera.Gain.Value = 30.0
        else:
            # software settings
            camera.TestImageSelector.SetValue("Testimage2")
            camera.PixelFormat.Value = "Mono16" 
            camera.TriggerSource.Value = "Software"
            
        # generic settings for both cases
        camera.ExposureTime.Value = 10000 # 10 ms
        camera.TriggerSelector.Value = "FrameStart"            
        camera.TriggerMode.Value = "On"

    except Exception as e:
        print(f"Error when configuring the camera: {e}")

def app_wrapper(autosave_flag, trigger_flag, smoothing):
    if not trigger_flag:
        os.environ["PYLON_CAMEMU"] = "1"

    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    EXTERNAL_TRIGGER = trigger_flag
    config_camera(camera, EXTERNAL_TRIGGER)


    ts = TriggeredSequence(autosave=autosave_flag, smoothing=smoothing)   
    
    # constant values
    num_images = 3
    figure_height = 300
    figure_width = 900

    w_ratio = figure_width // 3

    combined_image = np.zeros((figure_height, figure_width), dtype=np.uint16)

    def StartTriggerSequence(ts):
        # runtime values
        resized_images = []
        current_image_index = 0

        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        while camera.IsGrabbing():
            while current_image_index <= num_images:
                cv2.imshow('Combined Images', combined_image)
                if current_image_index == 3:
                    break
                key = cv2.waitKey(1)
                if key == 27:  # Esc key to exit
                    camera.StopGrabbing()
                    return False
                elif not EXTERNAL_TRIGGER and key == ord(" "):
                    camera.ExecuteSoftwareTrigger()

                # you cant check your key entry and wait for the next image in one thread at the same time,
                # so you can use this wait-object to check for new images and skip the 5 sec Timeout during RecieveResult
                if not camera.GetGrabResultWaitObject().Wait(10):
                    continue

                try:
                    # use the context handler, so you dont have to call "grabResult.Release" at the end
                    with camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException) as grabResult:
                        assert grabResult.GrabSucceeded()
                        # Accessing image data
                        img = grabResult.GetArray()
                        # images[img_type[current_image_index]] = img
                        ts.add_image(img)
                        img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)

                except pylon.TimeoutException as timeout_error:
                    raise AssertionError("Timeout error, this should not happen, "
                                         "because we waited for the image in the wait object before!") from timeout_error

                except AssertionError as assertion_error:
                    raise AssertionError("Unsuccessful grab, this should not happen at all!") from assertion_error

                # we dont need the capture flag variable anymore,
                # because of every image is grabbed on purpose, just add every incoming image
                resized_images.append(img.copy())
                for i in range(len(resized_images)):
                    h, w = resized_images[i].shape

                    resized_images[i] = cv2.resize(resized_images[i], (w_ratio, figure_height))
                    combined_image[0:figure_height, i * w_ratio: (i+1)* w_ratio] = resized_images[i]
                cv2.imshow('Combined Images', combined_image)
                current_image_index += 1

            camera.StopGrabbing()
            return True



    while True:
        try:
            if (StartTriggerSequence(ts)):
                ts.display_calculated_image()
            else:
                print("Software exit..")
                break
        except KeyboardInterrupt:
            print("Interrupted, exiting...")
            break
        # cv2.waitKey(1) # for software testing
    # camera.stopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()
    plt.close('all')
    return False