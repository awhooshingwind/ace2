from pypylon import pylon
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import trigger_seq

""" Define class for storing/displaying 3 triggered images, 
using image sequence to calculate corrected image,
then saving the resulting image as .txt file for analysis
Requires pypylon
"""

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

def trigger_mode(autosave_flag, trigger_flag, smoothing):
    if not trigger_flag:
        os.environ["PYLON_CAMEMU"] = "1"

    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    EXTERNAL_TRIGGER = trigger_flag
    config_camera(camera, EXTERNAL_TRIGGER)


    ts = trigger_seq.TriggeredSequence(autosave=autosave_flag, smoothing=smoothing)   
    
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
                if key == 27 or key == ord('q'):  # Esc key or q to exit
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