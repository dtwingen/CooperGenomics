import requests
import json
import sys
import local_settings
import datetime
import smtplib

now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days = 1)

print(now.strftime("%Y-%m-%d %H:%M:%S"))
print("Starting process...")

###
# Setup Information
###

# automatically manage cookies between requests
session = requests.Session()

# Enter your credentials
username = ""
password = ""
api_key = ""
email_user = ""
email_password = ""

if username == "" or password == "" or api_key == "" or email_user == "" or email_password == "":
    
    # look to see if there are credentials in local_settings.py
    username = local_settings.username
    password = local_settings.password
    api_key = local_settings.api_key

    if username == "" or password == "" or api_key == "":
        print("Please put in your credentials")
        sys.exit()

# Put in valid start time and endtime in EEN format.  
# All times in our system are in the UTC timezone.
# For example, November 21, 2018 01:23:45 AM would translate to 20181121012345.000
# (the last three digits are for microseconds)

start_time = yesterday.strftime("%Y%m%d")
end_time = yesterday.strftime("%Y%m%d")
noon_start = "120000.000"
noon_plus_1hr = "130000.000"
noon_end = "115959.999"

start_timestamp = start_time + noon_start
end_timestamp =   end_time + noon_plus_1hr

print(start_timestamp)
print(end_timestamp)

if start_timestamp == "" or end_timestamp == "":
    print("Please put in a start and ending time")
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

print ("Step 1 - Logging In: %s" % HTTP_STATUS_CODE[response.status_code])
token = response.json()['token']


###
# Step 2: login (part 2)
###

url = "https://login.eagleeyenetworks.com/g/aaa/authorize"

querystring = {"token": token}

payload = json.dumps({ 'token': token })
headers = {'content-type': 'application/json', 'authorization': api_key }

response = session.request("POST", url, data=payload, headers=headers)

print("Step 2 - Authorizing: %s" % HTTP_STATUS_CODE[response.status_code])

current_user = response.json()


###
# Step 3: get list of devices
###

url = "https://login.eagleeyenetworks.com/g/device/list"

payload = ""
headers = {'authorization': api_key }
response = session.request("GET", url, data=payload, headers=headers)

print("Step 3 - Getting List of Devices: %s" % HTTP_STATUS_CODE[response.status_code])

device_list = response.json()

# filter everything but the cameras
camera_id_list = [i[1] for i in device_list if i[3] == 'camera']

# Total # of cameras in the environment
camera_list_len = len(camera_id_list)

###
# Step 4: Iterate through all of the cameras and video lists, which we'll use to download the files
#         to the local directory in the next step.
###

def get_video_list(camera_id):
    url = "https://login.eagleeyenetworks.com/asset/list/video.flv"
        
    querystring = {"id": camera_id, "start_timestamp": start_timestamp, "end_timestamp": end_timestamp, "options": "coalesce"}
    payload = ""
    headers = {'authorization': api_key }
        
    response = session.request("GET", url, data=payload, params=querystring, headers=headers)

    video_list = response.json()

    return video_list

###
# Use these functions to create files containing device_list, camera_id_list, video_list info.
###

"""
def save_device_list_to_file(device_list):
    with open("device_list.txt", "w") as file:
        file.write(json.dumps(device_list))
    print("device_list.txt has been saved to file.")

def save_camera_id_list_to_file(camera_id_list):
    with open("camera_id_list.txt", "w") as file:
        for i in camera_id_list:
            file.write("%s\n" % i)

def save_video_list_to_file(video_list):
    with open("video_list", "w") as file:
        file.write(json.dumps(video_list))
    print("video_list saved as new file: 'video_list'.")


# Use the function below to recall the stored video list
def load_video_list_from_file(camera_id):
    with open(camera_id, "w") as file:
        video_list_read = file.read(json.loads(video_list))
    return video_list_read
"""

###
# Step 5: Download the files from the video_list to the local directory
###

def download_videos(camera_id,video_list):
    current_video = 0
    download_status = current_video + 1
    video_list_total = len(video_list)
    
    while current_video < video_list_total:
        download_status = current_video + 1
        print("Downloading video ", download_status, " of ", video_list_total)
        url = "https://login.eagleeyenetworks.com/asset/play/video.flv"

        querystring = {"id": camera_id, "start_timestamp": video_list[current_video]['s'], "end_timestamp": video_list[current_video]['e']}

        payload = ""
        headers = {'authorization': api_key}

        response = session.request("GET", url, data=payload, params=querystring, headers=headers)

        if response.status_code == 200:
            local_filename = "%s-%s.flv" % (camera_id, video_list[current_video]['e'])
            current_video += 1
            
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                    else:
                        print("error downloading last file...")
                        continue
    else:
        print("Finished downloading videos for camera_id " + camera_id + "...")


###
# Step 6: Initiate the script
###

print("Looking for videos to download...")

download_queue = 0

for camera_id in camera_id_list:
    if download_queue < camera_list_len:
        print("Found videos to download from camera_id " + camera_id)
        video_list_download = get_video_list(camera_id)
        download_videos(camera_id,video_list_download)
        download_queue += 1
    else:
        print("Downloads Finished. Have a nice day...")
