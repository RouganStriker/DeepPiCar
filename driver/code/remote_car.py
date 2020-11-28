import logging
import picar
import cv2
import datetime
from threading import Thread
from queue import Queue

import imutils
from imutils.video import WebcamVideoStream
from imutils.video import FPS
from pynput.keyboard import Key, Listener

_SHOW_IMAGE = True


class DeepPiCar(object):

    __INITIAL_SPEED = 0
    __SCREEN_WIDTH = 320
    __SCREEN_HEIGHT = 240

    def __init__(self):
        """ Init camera and wheels"""
        logging.info('Creating a DeepPiCar...')

        picar.setup()

        logging.debug('Set up camera')
        #self.camera = cv2.VideoCapture(-1)
        #self.camera.set(3, self.__SCREEN_WIDTH)
        #self.camera.set(4, self.__SCREEN_HEIGHT)
        self.camera = WebcamVideoStream(src=0).start()

        logging.debug('Set up back wheels')
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0  # Speed Range is 0 (stop) - 100 (fastest)

        logging.debug('Set up front wheels')
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turning_offset = -25  # calibrate servo to center
        self.angle = 90
        self.front_wheels.turn(90)  # Steering Range is 45 (left) - 90 (center) - 135 (right)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        datestr = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        self.video_orig = self.create_video_recorder('../data/tmp/car_video%s.avi' % datestr)
        
        self.fps = FPS().start()
        self.font = font = cv2.FONT_HERSHEY_SIMPLEX

        self.listener = Listener(on_press=self.on_keypress)
        #self.queue = Queue()
        logging.info('Created a DeepPiCar')
        #self.readThread = Thread(target=self.read_frame)
     
    def read_frame(self):
        while self.camera.isOpened():
            _, frame = self.camera.read()     
            self.queue.put(frame)

    def create_video_recorder(self, path):
        return cv2.VideoWriter(path, self.fourcc, 20.0, (self.__SCREEN_WIDTH, self.__SCREEN_HEIGHT))

    def __enter__(self):
        """ Entering a with statement """
        return self

    def __exit__(self, _type, value, traceback):
        """ Exit a with statement"""
        if traceback is not None:
            # Exception occurred:
            logging.error('Exiting with statement with exception %s' % traceback)

        self.cleanup()

    def cleanup(self):
        """ Reset the hardware"""
        logging.info('Stopping the car, resetting hardware.')
        self.back_wheels.speed = 0
        self.front_wheels.turn(90)
        #self.camera.release()
        self.fps.stop()
        self.camera.stop()
        self.video_orig.release()
        self.listener.stop()
        cv2.destroyAllWindows()

    def drive(self, speed=__INITIAL_SPEED):
        """ Main entry point of the car, and put it in drive mode

        Keyword arguments:
        speed -- speed of back wheel, range is 0 (stop) - 100 (fastest)
        """

        logging.info('Starting to drive at speed %s...' % speed)
        self.back_wheels.speed = speed
        self.listener.start()
       
        while True:
            frame = self.camera.read()
            frame = imutils.resize(frame, width=400)
            frame = imutils.rotate(frame, angle=180)

            current_fps = self.fps._numFrames /  (datetime.datetime.now() - self.fps._start).total_seconds()
            cv2.putText(frame, f'{int(current_fps)}FPS', (0, 25), self.font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow("Frame", frame)

            self.fps.update()
           
          
            #self.video_orig.write(image_lane)
            #show_image("Main", image_lane)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.cleanup()
                break 

    def on_keypress(self, key):
        if key == Key.left and self.angle > 45:
            self.angle -= 2
        elif key == Key.right and self.angle < 135:
            self.angle += 2
        else:
            return
        self.front_wheels.turn(self.angle)
        logging.info(f"Turning to {self.angle}")


############################
# Utility Functions
############################
def show_image(title, frame, show=_SHOW_IMAGE):
    if show:
        cv2.imshow(title, frame)


def main():
    with DeepPiCar() as car:
        car.drive(30)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)-5s:%(asctime)s: %(message)s')
    
    main()
