from pypylon import pylon
import os



""" Convenience module for configuring ace2 (or emulated) Basler camera

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

def emu_camera():
    os.environ["PYLON_CAMEMU"] = "1" # for emulated camera

    cam = init_camera()
    config_camera(cam, mode='SW')

    return cam
