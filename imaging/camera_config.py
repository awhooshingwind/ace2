from pypylon import pylon


""" Convenience module for setting up ace2 (or emulated) Basler camera

"""

def config_camera(camera, EXTERNAL_TRIGGER):
    try:
        # Set camera parameters for HW or software triggering
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
            camera.Width.Value = 1920
            camera.Height.Value = 1200
            
        # generic settings for both cases
        camera.ExposureTime.Value = 10000 # 10 ms
        camera.TriggerSelector.Value = "FrameStart"            
        camera.TriggerMode.Value = "On"

    except Exception as e:
        print(f"Error when configuring the camera: {e}")


def config_camera(camera, hw_trigger_mode):
    try:
        # setup camera for video mode
        camera.Open()
        
        if not hw_trigger_mode:
            camera.TestImageSelector.SetValue("Testimage2")
            camera.PixelFormat.Value = "Mono16" 
            
        else:
            camera.PixelFormat.Value = "Mono12p"
            camera.Gain.Value = 30.0

        # generic settings for both cases
        camera.ExposureTime.Value = 10000 # 10 ms

    except Exception as e:
        print(f"Error when configuring the camera: {e}")

def init_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    try:
        # Set camera parameters f
        camera.Open()
        # to get consistant results it is always good to start from "power-on" state
        camera.UserSetSelector.Value = "Default"
        camera.UserSetLoad.Execute()
        
        camera.PixelFormat.Value = "Mono12p"
        # camera.Gain.Value = camera_gain

    except Exception as e:
        print(f"Error when configuring the camera: {e}")
    
    return camera