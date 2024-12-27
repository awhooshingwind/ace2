import threading
from queue import Queue
from pypylon import pylon
import cv2
import numpy as np
import time
import imaging.camera_config as cc
import imaging.trig_seq as ts

class ImageHandler(pylon.ImageEventHandler):
    def __init__(self, image_queue):
        super().__init__()
        self.image_queue = image_queue
        self.image_count = 0
        self.img_list = []

    def OnImageGrabbed(self, camera, grabResult):
        try:
            if grabResult.GrabSucceeded():
                self.image_count += 1
                print(f'Grabbed {self.image_count}')
                img = grabResult.Array
                img = cv2.normalize(img, None, alpha=0, beta=65535, norm_type=cv2.NORM_MINMAX)
                self.image_queue.put(img)  # Add image to queue
                self.img_list.append(img)
            else:
                raise RuntimeError("Grab failed")
        except Exception as e:
            print(e)

def display_images(image_queue, stop_flag):
    """Continuously display images from the queue in the main thread."""
    combined_image = np.zeros((300, 1200), dtype=np.uint16)
    resized_imgs = []
    figw, figh = 1200, 300
    w_ratio = figw // 3

    cv2.imshow('Incoming Images', combined_image)
    
    while not stop_flag.is_set() or not image_queue.empty():
        if not image_queue.empty():
            img = image_queue.get()
            resized_img = cv2.resize(img, (w_ratio, figh))
            resized_imgs.append(resized_img)

            # Update the combined image
            for i, r_img in enumerate(resized_imgs):
                combined_image[0:figh, i * w_ratio:(i + 1) * w_ratio] = r_img

            cv2.imshow('Incoming Images', combined_image)
            # Use a small delay to keep the GUI responsive
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User requested exit.")
            stop_flag.set()  # Signal to stop the display thread
            break

        time.sleep(0.01)  # Prevent high CPU usage

    # print("Closing display...")
    cv2.destroyAllWindows()  # Ensure the window closes properly



def test_images():
    cam = cc.emu_camera()
    print(cam.GetDeviceInfo().GetModelName())

    image_queue = Queue()
    stop_flag = threading.Event()  # Flag to stop the display thread
    handler = ImageHandler(image_queue)

    try:
        cam.RegisterImageEventHandler(handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly, pylon.GrabLoop_ProvidedByInstantCamera)

        # Start the display thread
        display_thread = threading.Thread(target=display_images, args=(image_queue, stop_flag), daemon=True)
        display_thread.start()

        # Trigger images
        for _ in range(3):
            if cam.WaitForFrameTriggerReady(1000, pylon.TimeoutHandling_ThrowException):
                cam.ExecuteSoftwareTrigger()
                print('Trigger')
                time.sleep(0.8)

    except Exception as e:
        print(e)
    finally:
        cam.StopGrabbing()
        cam.DeregisterImageEventHandler(handler)
        cam.Close()  # Ensure the camera is properly closed

        stop_flag.set()  # Signal the display thread to stop
        display_thread.join()  # Wait for the display thread to finish

    return handler.img_list

def button_wrap():
    test = ts.TriggeredSequence()
    imgs = test_images()
    for img in imgs:
        test.add_image(img)

