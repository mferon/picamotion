#!/usr/bin/python

import datetime
import signal
import cv2
import picamera.array
import picamera
import os.path
import sys
import logging

CAMERA_WARM_UP_DURATION = 1000


class Picamotion:

    def __init__(self, framerate, width, height, gaussianKernelSize,
                 areaThreshold, pictureDirectory, addDateToPicture,
                 highlightDetectedChanges, savePictures):
        self.kill = False

        self.gaussianKernelSize = gaussianKernelSize
        self.previousFrame = None
        self.areaThreshold = areaThreshold
        self.pictureDirectory = pictureDirectory
        self.addDateToPicture = addDateToPicture
        self.highlightDetectedChanges = highlightDetectedChanges
        self.savePictures = savePictures

        if not os.path.isdir(self.pictureDirectory):
            raise ValueError(
                "Directory \"{}\" doesn't exist".format(self.pictureDirectory))

        if not self.gaussianKernelSize % 2:
            raise ValueError(
                "The gaussian kernel size must be an odd number ({})".format(
                    self.gaussianKernelSize))

        self.picameraInitTs = datetime.datetime.now()
        self.camera = picamera.PiCamera()
        self.camera.resolution = (width, height)
        self.camera.framerate = framerate
        self.rawCapture = picamera.array.PiRGBArray(self.camera,
                                                    size=(width, height))

        # Signal handler
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def __del__(self):
        try:
            self.camera.close()
        except AttributeError:
            pass

    def update_current_datetime(self):
        self.currentDateTime = datetime.datetime.now()

    def write_date_in_picture(self, picture):
        logging.debug('Write date in picture')
        cv2.putText(
            picture,
            self.currentDateTime.strftime("%A %d %B %Y %H:%M:%S.%f"),
            (10, picture.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (0, 0, 255), 1)

    def write_detected_change_highlight_in_picture(self, picture, contour):
        logging.debug('Write detected change in picture')
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(picture, (x, y), (x + w, y + h), (0, 255, 0), 1)

    def save_picture(self, picture):
        filename = '{}/picamotion_{}.jpg'.format(
            self.pictureDirectory,
            self.currentDateTime.strftime('%Y-%m-%d_%H-%M-%S-%f'),
        )
        if not cv2.imwrite(filename, picture):
            logging.warning('Unable to save picture to {}'.format(filename))
        else:
            logging.info('Picture saved to {}'.format(filename))

    def exit_gracefully(self, _signo, _stack_frame):
        logging.warning('SIGTERM received, exit ASAP')
        if self.kill:
            sys.exit(1)
        self.kill = True

    def waitPicamotionToBeReady(self):
        # Wait camera warm up
        logging.debug('Wait camera to be ready')
        ready = False
        while not ready:
            diff = datetime.datetime.now() - self.picameraInitTs
            diff = diff.total_seconds() * 1000
            ready = diff > CAMERA_WARM_UP_DURATION

    def start(self):

        self.waitPicamotionToBeReady()

        logging.info('Picamotion started')

        for frame in self.camera.capture_continuous(self.rawCapture,
                                                    format="bgr",
                                                    use_video_port=True):

            self.update_current_datetime()

            frame = frame.array

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(
                gray, (self.gaussianKernelSize, self.gaussianKernelSize), 0)

            self.rawCapture.truncate(0)

            if self.previousFrame is None:
                self.previousFrame = gray
                continue

            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(self.previousFrame, gray)
            thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)

            (contours, _) = cv2.findContours(
                thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            imageChanged = False

            # loop over the contours
            for contour in contours:
                # if the contour is too small, ignore it
                if cv2.contourArea(contour) < self.areaThreshold:
                    continue

                if self.highlightDetectedChanges:
                    self.write_detected_change_highlight_in_picture(
                        frame, contour)

                imageChanged = True

            if imageChanged:
                self.previousFrame = gray

                logging.info('Motion detected')

                if self.addDateToPicture:
                    self.write_date_in_picture(frame)

                if self.savePictures:
                    self.save_picture(frame)

            if self.kill:
                break
