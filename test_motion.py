#!/usr/bin/python

import picamotion
import argparse
import sys
import logging

MAX_LOG_LEVEL = 3

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--framerate",
                    type=int, default=30,
                    help="Framerate of the capture")
    ap.add_argument("-W", "--width",
                    type=int, default=752,
                    help="Width of the capture")
    ap.add_argument("-H", "--height",
                    type=int, default=480,
                    help="Height of the capture")
    ap.add_argument("-g", "--gaussian-kernel-size",
                    type=int, default=21,
                    help="Size of the gaussian kernel used to blur the image")
    ap.add_argument("-a", "--area-threshold",
                    type=int, default=2000,
                    help="Area threshold to consider as motion")
    ap.add_argument("-d", "--picture-directory",
                    type=str, default='.',
                    help="Directory to store picture")
    ap.add_argument("-D", "--add-date-to-picture",
                    action='store_true',
                    help="Add the date to pictures")
    ap.add_argument("-C", "--highlight-detected-changes",
                    action='store_true',
                    help="Add detected changes to pictures")
    ap.add_argument("-s", "--save-pictures",
                    action='store_true',
                    help="Save pictures")
    ap.add_argument('-v', '--verbose', action='count',
                    default=0,
                    help="Set the log level")
    args = vars(ap.parse_args())

    try:
        if args['verbose'] > MAX_LOG_LEVEL:
            raise argparse.ArgumentTypeError(
                "Maximum log level is {}".format(MAX_LOG_LEVEL))

        # Logging
        logging.basicConfig(level=(MAX_LOG_LEVEL-args['verbose'])*10,
                            format='[%(asctime)s][%(levelname)s] %(message)s')

        picamotion = picamotion.Picamotion(
            framerate=args['framerate'],
            width=args['width'],
            height=args['height'],
            gaussianKernelSize=args['gaussian_kernel_size'],
            areaThreshold=args['area_threshold'],
            pictureDirectory=args['picture_directory'],
            addDateToPicture=args['add_date_to_picture'],
            highlightDetectedChanges=args['highlight_detected_changes'],
            savePictures=args['save_pictures'],
        )

        picamotion.start()
    except Exception as e:
        logging.critical(str(e))
        sys.exit(1)
