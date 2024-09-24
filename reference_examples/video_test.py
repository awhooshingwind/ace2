import cv2


def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y, selected_point, gray_frame

    if event == cv2.EVENT_MOUSEMOVE:
        mouse_x, mouse_y = x, y
    elif event == cv2.EVENT_LBUTTONDOWN:
        selected_point = (x, y)

# Initialize the video capture object (0 for the default camera)
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Cannot open camera")
    exit()

cv2.namedWindow('Video Feed')
cv2.setMouseCallback('Video Feed', mouse_callback)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Convert frame to grayscale for intensity calculation
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display coordinates and intensity on the image
    info_text = f"Mouse Position: ({mouse_x}, {mouse_y})"
    cv2.putText(frame, info_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2)

    # Highlight the selected point
    if selected_point is not None:
        cv2.circle(frame, selected_point, 5, (0, 0, 255), -1)
        selected_intensity = gray_frame[selected_point[1], selected_point[0]]
        selected_text = f"Selected Point: {selected_point}"
        cv2.putText(frame, selected_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow('Video Feed', frame)

    # Wait for key press
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q') or key == 27:
        break
    # Fine-tune selected point with arrow keys
    elif key == 97:  # Left - a
        if selected_point:
            x = max(selected_point[0] - 1, 0)
            selected_point = (x, selected_point[1])
    elif key == 119:  # Up - w
        if selected_point:
            y = max(selected_point[1] - 1, 0)
            selected_point = (selected_point[0], y)
    elif key == 100:  # Right - d
        if selected_point:
            x = min(selected_point[0] + 1, frame.shape[1] - 1)
            selected_point = (x, selected_point[1])
    elif key == 115:  # Down - s
        if selected_point:
            y = min(selected_point[1] + 1, frame.shape[0] - 1)
            selected_point = (selected_point[0], y)

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
