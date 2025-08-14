"""Helper module for ace2 (or emulated) Basler camera

Handles configuration and imaging function,
triggered imaging works with single and absorption sequences
but code needs major refactoring for better modularity,
clarity, and reusability.

"""

import os
import cv2
import matplotlib.pyplot as plt
import numpy as np
from pypylon import pylon

# Base settings for absorption imaging
# TRIGGER_LINE = "Line1" 
# PIXEL_FORMAT = "Mono12p" # ace2 max
# GAIN = 23.0 # analog only gain, >= 24 applies digital gain
# EXPOSURE = 10000 # 10 ms

def init_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    try:
        # Set camera parameters
        camera.Open()
        # to get consistent results it is always good to start from "power-on" state
        camera.UserSetSelector.Value = "Default"
        camera.UserSetLoad.Execute()
    
    except Exception as e:
        print(f"Error when configuring the camera: {e}")
    finally:
        camera.Close()
    
    return camera

def config_camera(camera, mode='HW', exposure=10000, gain=23.0, trigger=True):
    try:
        camera.Open()
        # Set camera parameters for HW or software triggering
        camera.ExposureTime.Value = exposure

        if mode == 'HW':
            camera.TriggerSource.Value = "Line1"
            camera.PixelFormat.Value = "Mono12p"
            camera.Gain.Value = gain
            print('hw mode setup')

        if mode == 'SW':
            # software settings
            camera.TestImageSelector.SetValue("Testimage2") # Simple gradient
            # Uncomment below for custom images, check image dir path
            # camera.TestImageSelector.Value = 'Off'
            # camera.ImageFileMode.Value = 'On'
            # camera.ImageFilename.Value = "C:\\Users\\jakep\\Projects\\ace2\\testimages\\"
            camera.PixelFormat.Value = "Mono16" 
            camera.TriggerSource.Value = "Software"
            camera.Width.Value = 1024
            camera.Height.Value = 1040 
            print('sw mode setup')
        
        if trigger:
            # generic settings for both trigger cases
            camera.TriggerSelector.Value = "FrameStart"            
            camera.TriggerMode.Value = "On"
            print(camera.TriggerMode.Value)

    except Exception as e:
        print(f"Error when configuring the camera: {e}")
    print('config ok')

def emu_camera(trigger=True):
    os.environ["PYLON_CAMEMU"] = "1" # for emulated camera

    cam = init_camera()
    config_camera(cam, mode='SW', trigger=trigger)

    return cam

def trigger_mode(hw_mode, ts):
    if not hw_mode:
        camera = emu_camera() # for emulated camera
    else:
        camera = init_camera()
        config_camera(camera)

    num_images = 3 # for absorption imaging sequence
    def StartTriggerSequence(ts):
        # runtime values
        current_image_index = 0
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while camera.IsGrabbing():
            while current_image_index <= num_images:
                cv2.imshow('Triggered_Images', ts.combined_image)
                key = cv2.waitKey(1)
                if key == 27 or key == ord('q'):  # Esc key or q to exit
                    camera.StopGrabbing()
                    return False
                elif not hw_mode and key == ord(" "):
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
                        ts.add_image(img)
                        # img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)
                except pylon.TimeoutException as timeout_error:
                    raise AssertionError("Timeout error, this should not happen, "
                                         "because we waited for the image in the wait object before!") from timeout_error
                except AssertionError as assertion_error:
                    raise AssertionError("Unsuccessful grab, this should not happen at all!") from assertion_error
                current_image_index += 1
                if current_image_index == 4:
                    break
            camera.StopGrabbing()
            return True

    while True:
        try:
            if not (StartTriggerSequence(ts)):
                print("Software exit..")
                break
        except KeyboardInterrupt:
            print("Interrupted, exiting...")
            break

    camera.Close()
    cv2.destroyAllWindows()
    plt.close('all')
    return False

""" Video mode with movable onscreen cursor for alignment"""
def video_mode(hw_mode=True):
    # Cursor variables
    mouse_x, mouse_y = 0, 0
    selected_point = None
    # Helpers
    def adjust_image(img, brightness=0, contrast=0):
        """
        Adjust the brightness and contrast of an image via trackbar sliders
        range: -255 to 255 (0= no change)
        """
        brightness = np.clip(brightness, -255, 255)
        contrast = np.clip(contrast, -255, 255)
        # Adjust brightness
        if brightness != 0:
            img = np.int16(img) + brightness
            img = np.clip(img, 0, 255).astype(np.uint8)
        # Adjust contrast
        if contrast != 0:
            factor = (259*(contrast + 255)) / (255 * (259-contrast))
            img = np.clip(factor * (np.int16(img) - 128) + 128, 0, 255).astype(np.uint8)
        
        return img

    def mouse_callback(event, x, y, flags, param):
        nonlocal mouse_x, mouse_y, selected_point
        if event == cv2.EVENT_MOUSEMOVE:
            mouse_x, mouse_y = x, y
        elif event == cv2.EVENT_LBUTTONDOWN:
            selected_point = (x, y)
    
    if not hw_mode:
        camera = emu_camera(trigger=False) # for emulated camera
    else:
        camera = init_camera()
        config_camera(camera, trigger=False)

    # Grabbing Continuously (video) with minimal delay
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    converter = pylon.ImageFormatConverter()
    # Converting to OpenCV BGR format
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    # Trackbar helper functions
    def change_brightness(val):
        nonlocal brightness
        brightness = val - 255 # shift into range [-255, 255]
    def change_contrast(val):
        nonlocal contrast
        contrast = val - 255 
    def toggle_cmap(val):
        nonlocal cmap_flag
        cmap_flag = bool(val)
    # initialize variables
    brightness = 0
    contrast = 0
    cmap_flag = False

    # Video Window with trackbar
    cv2.namedWindow('Video Feed', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Video Feed', mouse_callback)
    # cv2.namedWindow('Controls', cv2.WINDOW_NORMAL) # controls in separate window??
    cv2.createTrackbar('Brightness', 'Video Feed', 255, 510, change_brightness)
    cv2.createTrackbar('Contrast', 'Video Feed', 255, 510, change_contrast)
    cv2.createTrackbar('Colormap', 'Video Feed', 0, 1, toggle_cmap)
    # cv2.resizeWindow('Controls', 300, 2)
    cv2.resizeWindow('Video Feed', 1100, 1300)
    
    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            # Access the image data
            image = converter.Convert(grabResult)
            frame = image.GetArray() 
            # update frame with adjustments
            frame = adjust_image(frame, brightness, contrast)
            # Show the frame
            if cmap_flag:
                frame = cv2.applyColorMap(frame, cv2.COLORMAP_VIRIDIS)
             # Display coordinates and intensity on the image
            info_text = f"Mouse Position: ({mouse_x}, {mouse_y})"
            cv2.putText(frame, info_text, (10, 20), cv2.FONT_HERSHEY_COMPLEX,
                        0.7, (226, 80, 55), 2)
    
            # Highlight the selected point
            if selected_point is not None:
                cv2.circle(frame, selected_point, 5, (0, 60, 155), -1)
                selected_text = f"Selected Point: {selected_point}"
                cv2.putText(frame, selected_text, (10, 50), cv2.FONT_HERSHEY_COMPLEX,
                            0.8, (50, 30, 152), 2)    
            cv2.imshow('Video Feed', frame)
            # Wait for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27: # Exit with q or esc
                break
            # Fine-tune selected point with 'a', 'w', 'd', 's' keys
            elif key == ord('a'):  # Left
                if selected_point:
                    x = max(selected_point[0] - 1, 0)
                    selected_point = (x, selected_point[1])
            elif key == ord('w'):  # Up
                if selected_point:
                    y = max(selected_point[1] - 1, 0)
                    selected_point = (selected_point[0], y)
            elif key == ord('d'):  # Right
                if selected_point:
                    x = min(selected_point[0] + 1, frame.shape[1] - 1)
                    selected_point = (x, selected_point[1])
            elif key == ord('s'):  # Down
                if selected_point:
                    y = min(selected_point[1] + 1, frame.shape[0] - 1)
                    selected_point = (selected_point[0], y)
        # else:
        #     print("Grab Failed")
    
        # Release the grab result in all cases
        grabResult.Release()
    # Releasing the resource
    camera.Close()
    cv2.destroyAllWindows()


def take_dark_frame():
    """ From a dark frame, determine locations of 'hot pixels' and save coordinates. 
    
    From those coordinates, generate a mask to correct for hot pixels 
    in subsequent frames (or use Basler built-in pixel defect correction...)
    """
    camera = init_camera()
    camera.Open()
    camera.PixelFormat.Value = "Mono12p"
    camera.Gain.Value = 48.0 # Max Gain
    camera.ExposureTime.Value = 10000000 # max exposure (10s)

    camera.StartGrabbingMax(1)
    try:
        while camera.IsGrabbing():
            # for exposure in exposure_times:
            # for i in range(num_frames)
                # camera.ExposureTime.Value = exposure
                # use the context handler, so you dont have to call "grabResult.Release" at the end
            with camera.RetrieveResult(int(10000000+1000), pylon.TimeoutHandling_ThrowException) as grabResult:
                if grabResult.GrabSucceeded():    
                    # Accessing image data
                    img = grabResult.GetArray()
                    print(f"img grabbed")     
    except Exception as e:
        print(f"Error {e}")   
         
    camera.StopGrabbing()
    camera.Close()
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

