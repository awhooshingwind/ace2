from pypylon import pylon
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
from imaging import trig_seq
from imaging import camera_config as cc

""" Define class for storing/displaying 3 triggered images, 
using image sequence to calculate corrected image,
then saving the resulting image as .txt file for analysis
Requires pypylon
"""


def trigger_mode(trigger_flag, ts):

    if not trigger_flag:
        camera = cc.emu_camera() # for emulated camera
    
    else:
        camera = cc.init_camera()
        cc.config_camera(camera)
 
    # constant values
    num_images = 3
 
    def StartTriggerSequence(ts):
        # runtime values
        current_image_index = 0

        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        while camera.IsGrabbing():
            while current_image_index <= num_images:
                cv2.imshow('Triggered_Images', ts.combined_image)
                if current_image_index == 3:
                    break
                key = cv2.waitKey(1)
                if key == 27 or key == ord('q'):  # Esc key or q to exit
                    camera.StopGrabbing()
                    return False
                elif not trigger_flag and key == ord(" "):
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
                        # img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)

                except pylon.TimeoutException as timeout_error:
                    raise AssertionError("Timeout error, this should not happen, "
                                         "because we waited for the image in the wait object before!") from timeout_error

                except AssertionError as assertion_error:
                    raise AssertionError("Unsuccessful grab, this should not happen at all!") from assertion_error

                current_image_index += 1

            camera.StopGrabbing()
            return True

    while True:
        try:
            if (StartTriggerSequence(ts)):
                print('yay')
            else:
                print("Software exit..")
                break
        except KeyboardInterrupt:
            print("Interrupted, exiting...")
            break

    camera.Close()
    cv2.destroyAllWindows()
    plt.close('all')
    return False
