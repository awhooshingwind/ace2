from pypylon import pylon
import os
import cv2
import matplotlib.pyplot as plt
import numpy as np


""" Convenience functions for configuring ace2 (or emulated) Basler camera

"""

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
            camera.TestImageSelector.SetValue("Testimage2")
            camera.PixelFormat.Value = "Mono16" 
            camera.TriggerSource.Value = "Software"
            camera.Width.Value = 1920
            camera.Height.Value = 1200 
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


""" Define class for storing/displaying 3 triggered images, 
using image sequence to calculate corrected image,
then saving the resulting image as .txt file for analysis
Requires pypylon
"""

def trigger_mode(trigger_flag, ts):

    if not trigger_flag:
        camera = emu_camera() # for emulated camera
    
    else:
        camera = init_camera()
        config_camera(camera)
 
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

""" Video mode with movable onscreen cursor for alignment
"""
def video_mode(hw_mode=True):

    # Cursor variables
    mouse_x, mouse_y = 0, 0
    selected_point = None

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
    
    cv2.namedWindow('Video Feed', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Video Feed', mouse_callback)
    
    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    
        if grabResult.GrabSucceeded():
            # Access the image data
            image = converter.Convert(grabResult)
            frame = image.GetArray()
    
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
    
            # Show the frame
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
    
        else:
            print("Grab Failed")
    
        # Release the grab result in all cases
        grabResult.Release()
    
    # Releasing the resource
    camera.Close()
    cv2.destroyAllWindows()


    """ From a dark frame, determine locations of 'hot pixels' and save coordinates. From those coordinates, generate a mask to correct for hot pixels in subsequent frames (or use Basler built-in pixel defect correction...)
"""

def take_dark_frame():
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
'''
## TESTING
# Compare dark frames taken with different gain values (max at 40, max analog at 23)
with open('./noise/b10101.npy', 'rb') as f:
    dark_frame = np.load(f)
    hot40 = find_hot_pixel(dark_frame, save=True)

with open('./noise/b10101_23gain.npy', 'rb') as f:
    dark_frame_23 = np.load(f)
    hot23 = find_hot_pixel(dark_frame_23)

# Find the common hot pixels for sanity check
common_hot_pixels = np.intersect1d(hot40.view([('', hot40.dtype)] * hot40.shape[1]),
                                   hot23.view([('', hot23.dtype)] * hot23.shape[1]))

# Convert the result back to regular coordinates
common_hot_pixels = common_hot_pixels.view(hot40.dtype).reshape(-1, 2)
# print(np.equal(common_hot_pixels, hot23))
# print(common_hot_pixels.shape)

'''
