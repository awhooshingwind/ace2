from pypylon import pylon
import os
import cv2


def config_camera(camera, hw_trigger_mode):
    try:
        # setup camera aoi
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


def video_mode(hw_trigger=True):

    # Global variables
    mouse_x, mouse_y = 0, 0
    selected_point = None

    def mouse_callback(event, x, y, flags, param):
        nonlocal mouse_x, mouse_y, selected_point

        if event == cv2.EVENT_MOUSEMOVE:
            mouse_x, mouse_y = x, y
        elif event == cv2.EVENT_LBUTTONDOWN:
            selected_point = (x, y)
    
        # TESTING
    if not hw_trigger:
        os.environ["PYLON_CAMEMU"] = "1"

    # Make Basler camera
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    config_camera(camera, hw_trigger)

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
            cv2.putText(frame, info_text, (10, 20), cv2.FONT_HERSHEY_DUPLEX,
                        0.7, (255, 15, 5), 2)
    
            # Highlight the selected point
            if selected_point is not None:
                cv2.circle(frame, selected_point, 5, (0, 60, 155), -1)
                selected_text = f"Selected Point: {selected_point}"
                cv2.putText(frame, selected_text, (10, 50), cv2.FONT_HERSHEY_DUPLEX,
                            0.8, (0, 55, 160), 2)
    
            # Show the frame
            cv2.imshow('Video Feed', frame)
    
            # Wait for key press
            key = cv2.waitKey(1) & 0xFF
    
            if key == ord('q') or key == 27:
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
