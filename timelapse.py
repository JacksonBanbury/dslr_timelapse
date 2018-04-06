'''
Created for use with the Canon EOS 1300D (Rebel T6) for timelapse photography.

Written for python3 with python3-gphoto2

Thanks to Jim Easterbrook's python-gphoto2 library and example code:
https://github.com/jim-easterbrook/python-gphoto2

Redistributed under the GNU General Public License - GPL v3.0
See: https://www.gnu.org/licenses/gpl-3.0.en.html

Jackson Banbury
April, 2018
'''

import logging
import os
import subprocess
import sys
from datetime import datetime
import time

import gphoto2 as gp

def send_scp(save_path, filename):
    #This function can be used to send the images from the camera
    #to a remote storage location via SCP

    #Define your destination path here (on the remote machine):
    dest_path = 'username@192.168.1.10:~/path/to/save/location'

    file_target = os.path.join(save_path, filename)
    p = subprocess.Popen(["scp", file_target, dest_path])
    sts = os.waitpid(p.pid, 0)

def capture(save_path, filename):
    #log to be used by gphoto
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    gp.check_result(gp.use_python_logging())
    context = gp.gp_context_new()
    camera = gp.check_result(gp.gp_camera_new())
    gp.check_result(gp.gp_camera_init(camera))

    config = camera.get_config(context)
    target = config.get_child_by_name('viewfinder')
    target.set_value(1)
    camera.set_config(config, context)
    target.set_value(0)
    camera.set_config(config, context)

    time.sleep(2)

    #capture the image (to camera's internal SD card)
    file_path = gp.check_result(gp.gp_camera_capture(
        camera, gp.GP_CAPTURE_IMAGE))

    #Copy the image over usb to the local filesystem
    target = os.path.join(save_path, filename)
    camera_file = gp.check_result(gp.gp_camera_file_get(
            camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))

    gp.gp_file_save(camera_file, target)

    #exit the camera to complete the process
    gp.gp_camera_exit(camera)
    return 0


def timelapse():
    #Define the time interval during daylight and nighttime here (minutes):
    day_interval = 5
    night_interval = 1
    sunrise_sunset_interval = 2

    #Set the local sunrise/sunset hours (24 hr format):
    sunrise_hour = 6
    sunrise_minute = 57
    sunset_hour = 20
    sunset_minute = 46

    #Image number for writing successive filenames
    img_number = 0

    #Begin the timelapse loop
    while(True):
        #Change your desired save directory here
        save_path = '/home/pi/timelapse'

        #Filename holds 4 digits - leading zeros allows for proper sorting
        filename = 'timelapse%04d.JPG'%img_number

        #Get the proper interval based on the current time
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute

        #Near sunrise and sunset, a separate interval is used
        if(current_hour==sunrise_hour and abs(current_minute-sunrise_minute)<=5):
            interval=sunrise_sunset_interval
        elif(current_hour==sunset_hour and abs(current_minute-sunset_minute)<=5):
            interval=sunrise_sunset_interval
        elif(current_hour>=sunrise_hour and current_hour<sunset_hour):
            interval = day_interval
        else:
            interval = night_interval

        #Wait aforementioned interval before taking photo
        #(remember time.sleep takes seconds)
        time.sleep(interval*60)

        #capture the photo (with proper filename)
        capture(filename)

        #send the file over scp to server storage
        send_scp(save_path, filename)


if __name__ == "__main__":
    timelapse()
