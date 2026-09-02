import cv2


class CameraInput:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            return None

        # Resize frame
        frame = cv2.resize(frame, (640, 480))

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return rgb_frame

    def release(self):
        self.cap.release()


# Test the camera module
if __name__ == "__main__":

    camera = CameraInput()

    print("Camera started successfully!")
    print("Press 'q' to quit.")

    while True:
        frame = camera.get_frame()

        if frame is None:
            print("Could not read frame")
            break

        print(frame.shape)

        # Convert RGB back to BGR for OpenCV display
        display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        cv2.imshow("Driver Monitoring Camera", display_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()