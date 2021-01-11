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
print("Step 1 - Logging In: %s" % HTTP_STATUS_CODE[response.status_code])

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
print("Step 2 - Authorizing: %s" % HTTP_STATUS_CODE[response.status_code])

current_user = response.json()

###
# Step 3: get list of devices
###


url = "https://login.eagleeyenetworks.com/g/device/list"

payload = ""
headers = {'authorization': api_key }
response = session.request("GET", url, data=payload, headers=headers)

logging.debug("Step 3 - Getting List of Devices: %s" % HTTP_STATUS_CODE[response.status_code])
print("Step 3 - Getting List of Devices: %s" % HTTP_STATUS_CODE[response.status_code])

device_list = response.json()

"""
# filter by camera ID
camera_id_list = [i[1] for i in device_list if i[3] == 'camera']
"""

# filter by friendly camera name
friendly_id_list = [i[2] for i in device_list if i[3] == 'camera']

camera_id_list = ['100b2a71','10037e74','100b30cf','100badd7','1000f51e','1009a8c0','10058861','10014836','1003583a','100a9f81','100cbc5e','10039a34','1000f643','100bfd8e','1000865b','100f7ece','10098f7d','100cb05a','100584b3','100db5e9','100aa5c0','10070ab7','100b5101','1000a17b','10046c9d','10079d92','100404fc','100a16e7','10013cd9']



# count of cameras found in the environment
camera_list_len = len(camera_id_list)
logging.debug("Found %s cameras..." % camera_list_len)
print("Found %s cameras..." % camera_list_len)

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

###
# Step 4: Fetch video files to download for each camera
###

# Check if directory exists to save video files
def check_directory_create(current_wd,start_time):
    archive_dir = os.path.abspath("\%s-archive" % (start_time))
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)
        print("Creating new directory %s to save files downloaded from today." % (archive_dir))
        return archive_dir
    else:
        print("Directory %s already exists... files downloaded today will be saved to this directory." % (archive_dir))
        return archive_dir

check_directory_create(current_wd, start_time)

logging.debug("Step 4: Gathering list of videos to download for each camera...")
print("Step 4: Gathering list of videos to download for each camera...")

session_list = {}

download_path = check_directory_create(current_wd,start_time)

for camera_id in camera_id_list:
    video_list = get_video_list(camera_id)
    video_list_len = len(video_list)
    if video_list_len > 1:
        print("Found %s videos to download for camera %s" % (video_list_len, camera_id))
        session_list[camera_id] = video_list
    else:
        print("No videos found for camera %s. Skipping..." % camera_id)

camera_ids_with_files = len(session_list)
print("%s of %s cameras have video files ready to download." % (camera_ids_with_files, camera_list_len))

# Create text file that lists the video files to download
session_list_file = []

with open("%s-video-list.txt" % (yesterday_friendly), "w") as file:
    for camera in camera_id_list:
        download_len = len(get_video_list(camera))
        if download_len > 0:
            session_list_file.append(get_video_list(camera))
            file.writelines(str(get_video_list(camera)))
        else:
            continue

def get_session_list():
    return session_list
    
print("created file %s-video-list.txt" % (yesterday_friendly))

print("all files created successfully - ready to proceed to download step.")

download_path = current_wd

for camera_id in camera_id_list:
    video_list = get_video_list(camera_id)
    video_list_len = len(video_list)
    
print("Step 5: Uploading files to AWS")
def upload_to_aws(file_name, bucket=local_settings.bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def download_videos(archive_path,camera_id,video_list):
    current_video = 0
    download_status = current_video + 1
       
    while current_video < len(video_list):
        download_status = current_video + 1
        print("Downloading video %s of %s..." % (download_status, len(video_list)))
        url = "https://login.eagleeyenetworks.com/asset/play/video.flv"

        querystring = {"id": camera_id, "start_timestamp": video_list[current_video]['s'], "end_timestamp": video_list[current_video]['e']}

        payload = ""
        headers = {'authorization': api_key}

        response = session.request("GET", url, data=payload, params=querystring, headers=headers, stream=True)
        response.raise_for_status()
        print(HTTP_STATUS_CODE[response.status_code])


        if response.status_code == 200:
            local_filename = "%s-%s.flv" % (camera_id, video_list[current_video]['e'])
            local_path = ("%s\%s" % (output_dir, local_filename))
            current_video += 1
            
            with open(local_path, "wb") as f:
                total_length = int(response.headers.get('content-length'))
                for chunk in progress.bar(response.iter_content(chunk_size=8192), expected_size=(total_length/8192) + 1):
                    if chunk:
                        f.write(chunk)
                        # f.flush()
                        with open("%s_%s_output.txt" % (yesterday_friendly, now_friendly), "w") as file:
                            file.write("%s/%s \n" % (output_dir, local_filename))
                    else:
                        print("error downloading last file...")    
                        
            if upload_to_aws(local_path,bucket=local_settings.bucket) == True:
                print("%s has been uploaded to the S3 bucket successfully" % local_filename)
            else:
                S3_errors = "%s-errors.txt" % start_time
                with open(S3_errors, "w") as errors:
                    errors.write("%s \n" % local_path)
                    print("error_logged")                                
        else:
            print("HTTP Status Code: %s" % HTTP_STATUS_CODE[response.status_code])
    print("Finished downloading videos for camera_id %s ..." % camera_id)

for key in session_list:
    print("Initializing download of %s video files for camera %s" % (len(session_list[key]), key))
    try:
        download_videos(download_path, key, session_list[key])
    except Exception as e:
        logging.debug("Exception occured: %s" % e)
        print("Error - Exception occured: %s" % e)

print("Downloads complete - exiting process...")
sys.exit()

