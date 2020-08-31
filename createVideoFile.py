import requests
import json
import sys
import datetime
import logging
import os
# import file containing api credentials
import local_settings
# import progress bar module
from clint.textui import progress
# import aws module for sending files to S3 bucket
import boto3
from botocore.exceptions import ClientError

# Valid start time and end time must be in EEN format.  

# All times in the EEN system use the UTC timezone.

# For example, November 21, 2018 01:23:45 AM would translate to 20181121012345.000

# The last 3 digits are for microseconds and are required.


# Required datetime variables
now = datetime.datetime.now()
now_friendly = now.strftime("%m%d%Y")
yesterday = now - datetime.timedelta(days = 1)
yesterday_friendly = yesterday.strftime("%m%d%Y")
start_time = yesterday.strftime("%Y%m%d")
end_time = now.strftime("%Y%m%d")

# (now.strftime("%Y-%m-%d %H:%M:%S"))


###
# UNCOMMENT BELOW SECTION AND REPLACE TESTING SECTION WHEN IN PRODUCTION
###

# start_timestamp and end_timestamp below are values to be used in production - 24 hour fetch period

noon_start = "120000.000"
noon_end = "115959.999"

start_timestamp = start_time + noon_start
end_timestamp =   end_time + noon_end
noon_friendly = "12:00 UTC"
end_noon_friendly = "11:59 UTC"
start_friendly = ("%s %s" % (yesterday_friendly, noon_friendly))
end_friendly = ("%s %s" % (now_friendly, end_noon_friendly))

if start_timestamp == "" or end_timestamp == "":
    print("Please put in a start and ending time")
    sys.exit()

print("Fetching video files captured between %s and %s..." % (start_friendly, end_friendly))

###
# END PRODUCTION SECTION
###

###
# THIS SECTION TO BE USED FOR TESTING PURPOSES ONLY
###
"""
test_start = "120000.000"
test_end = "130000.000"
test_start_friendly = "12:00 UTC"
test_end_friendly = "13:00 UTC" 

start_timestamp = start_time + test_start
end_timestamp = end_time + test_end

if start_timestamp == "" or end_timestamp == "":
    logging.ERROR("Please put in a start and ending time")
    sys.exit()

# print("Fetching video files captured on %s between %s and %s" % (yesterday_friendly, test_start_friendly, test_end_friendly))
"""
###
# END TESTING SECTION - COMMENT/REMOVE THIS ENTIRE SECTION WHEN IN PRODUCTION
###

###
# Setup Information
###

logging.basicConfig(filename="debug.log", level=logging.DEBUG)

# get directory PATHs
parent_dir = os.path
current_wd = os.getcwd()
script_path = "createVideoFile.py"
logging.debug("The parent directory for the current running script is %s" % parent_dir)
logging.debug("The current working directory is %s" % current_wd)

# verify required directories exist
parent_output_dir = "%s\\output" % (parent_dir)
working_output_dir = "%s\\output" % (current_wd)

logging.debug("Checking for required directory paths...")
output_dir = os.path.abspath("output")
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
    logging.debug("created OUTPUT directory - %s" % output_dir)
else:
    logging.debug("OK")

archive_dir = os.path.abspath("\%s-archive" % (start_time))
if not os.path.exists(archive_dir):
    os.mkdir(archive_dir)
    logging.debug("Creating new directory %s to save files downloaded from today." % (archive_dir))
else:
    logging.debug("Directory %s already exists... files downloaded today will be saved to this directory." % (archive_dir))

# automatically manage cookies between requests
session = requests.Session()

# Enter your credentials
username = ""
password = ""
api_key = ""

if username == "" or password == "" or api_key == "":
    
    # look to see if there are credentials in local_settings.py
    username = local_settings.username
    password = local_settings.password
    api_key = local_settings.api_key

    if username == "" or password == "" or api_key == "":
        logging.ERROR("Please put in your credentials")
        sys.exit()



# Translating the HTTP response codes to make the status messages easier to read
HTTP_STATUS_CODE = { 
    200: 'OK', 
    202: 'ACCEPTED',
    400: 'Bad Request, please check what you are sending',
    401: 'User needs to Login first', 
    403: 'User does not have access to that',
    500: 'API had a problem (500)',
    502: 'API had a problem (502)',
    503: 'API had a problem (503)'
    }

###
# Step 1: login (part 1)
# make sure put in valid credentials
###

url = "https://login.eagleeyenetworks.com/g/aaa/authenticate"

payload = json.dumps({'username': username, 'password': password})
headers = {'content-type': 'application/json', 'authorization': api_key }

response = session.request("POST", url, data=payload, headers=headers)

logging.debug("Step 1 - Logging In: %s" % HTTP_STATUS_CODE[response.status_code])

token = response.json()['token']

###
# Step 2: login (part 2)
###

url = "https://login.eagleeyenetworks.com/g/aaa/authorize"

querystring = {"token": token}

payload = json.dumps({ 'token': token })
headers = {'content-type': 'application/json', 'authorization': api_key }

response = session.request("POST", url, data=payload, headers=headers)

logging.debug("Step 2 - Authorizing: %s" % HTTP_STATUS_CODE[response.status_code])

current_user = response.json()

###
# Step 3: get list of devices
###


url = "https://login.eagleeyenetworks.com/g/device/list"

payload = ""
headers = {'authorization': api_key }
response = session.request("GET", url, data=payload, headers=headers)

logging.debug("Step 3 - Getting List of Devices: %s" % HTTP_STATUS_CODE[response.status_code])

device_list = response.json()

# filter by camera ID
camera_id_list = [i[1] for i in device_list if i[3] == 'camera']

# filter by friendly camera name
friendly_id_list = [i[2] for i in device_list if i[3] == 'camera']

# count of cameras found in the environment
camera_list_len = len(camera_id_list)
logging.debug("Found %s cameras..." % camera_list_len)

"""
# create merged list with camera ID and friendly camera name
merged_camera_list = [i+'_'+j for i,j in zip(camera_id_list,friendly_id_list)]
''.join(merged_camera_list)
logging.debug(merged_camera_list)
"""

# Given a specific camera_id, fetch a list of video files.
def get_video_list(camera_id):
    url = "https://login.eagleeyenetworks.com/asset/list/video.flv"
        
    querystring = {"id": camera_id, "start_timestamp": start_timestamp, "end_timestamp": end_timestamp, "options": "coalesce"}
    payload = ""
    headers = {'authorization': api_key }
        
    response = session.request("GET", url, data=payload, params=querystring, headers=headers)

    video_list = response.json()

    return video_list

# create summary file w/ count of videos for each camera_id
logging.debug("creating file w/ count of videos to download per camera_id")
total_videos = 0

with open("%s-download-summary.txt" % (yesterday_friendly), "w") as file:
    for camera in camera_id_list:
        download_len = len(get_video_list(camera))
        file.write("%s: %s \n" %(camera, download_len))
        total_videos += download_len
    file.write("Total # of videos to download: %s" % total_videos)

print("created file %s-download-summary.txt" % yesterday_friendly)

###
# Step 4: Fetch video files to download for each camera
###

session_list = []

# Create text file that lists the video files to download
with open("%s-video-list.txt" % (yesterday_friendly), "w") as file:
    for camera in camera_id_list:
        download_len = len(get_video_list(camera))
        if download_len > 0:
            session_list.append(get_video_list(camera))
            file.writelines(str(get_video_list(camera)))
        else:
            continue

def get_session_list():
    return session_list
    
print("created file %s-video-list.txt" % (yesterday_friendly))

print("all files created successfully - ready to proceed to download step.")