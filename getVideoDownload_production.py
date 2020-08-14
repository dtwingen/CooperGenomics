import requests
import json
import sys
import datetime
import logging
import os
# import necessary packages for email notifications
import smtplib
# import template for email notification
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# import file containing api credentials
import local_settings
# import file containing smtp credentials
import smtp_settings
# import progress bar module
from clint.textui import progress
# import aws module for sending files to S3 bucket
import boto3
from botocore.exceptions import ClientError

###
# Setup Information
###

# get directory PATHs
parent_dir = os.path
current_wd = os.getcwd()
script_path = "getVideoDownload_production.py"
print("The parent directory for the currently running script is %s" % parent_dir)
print("The current working directory is %s" % current_wd)

# verify required directories exist
parent_output_dir = "%s\\output" % (parent_dir)
working_output_dir = "%s\\output" % (current_wd)
print(parent_output_dir)
print(working_output_dir)

print("Checking for required directory paths...")
output_dir = os.path.abspath("output")
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
    print("created OUTPUT directory - %s" % output_dir)
else:
    print("OK")

# automatically manage cookies between requests
session = requests.Session()

# Enter your credentials
username = ""
password = ""
api_key = ""
smtp_host = ""
smtp_port = ""
smtp_email = ""
smtp_password = ""

if username == "" or password == "" or api_key == "":
    
    # look to see if there are credentials in local_settings.py
    username = local_settings.username
    password = local_settings.password
    api_key = local_settings.api_key

    if username == "" or password == "" or api_key == "":
        print("Please put in your credentials")
        sys.exit()

if smtp_host == "" or smtp_port == "" or smtp_email == "" or smtp_password == "":

    # look to see if there are credentials in smtp_settings.py
    smtp_host = smtp_settings.smtp_host
    smtp_port = smtp_settings.smtp_port
    smtp_email = smtp_settings.smtp_email
    smtp_password = smtp_settings.smtp_password

    if smtp_host == "" or smtp_port == "" or smtp_email == "" or smtp_password == "":
        print("Please put in SMTP credentials for email notifications")
        sys.exit()

###
# Set up the email notification service
###

def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """
    
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails

def read_template(filename):
    """
    Returns a Template object comprising the contents of the
    file specified by filename.
    """

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

# Read contacts
def main():
    names, emails = get_contacts('email_contacts.txt')
    message_template = read_template('message.txt')
    
    # Set up the SMTP server
    s = smtplib.SMTP(host=smtp_host, port=smtp_port)
    s.starttls()
    s.login(smtp_email, smtp_password)

    # For each contact, send the email:
    for name, email in zip(names, emails):
        # Create a message
        msg = MIMEMultipart()

        # Add the actual person name to the message template
        message = message_template.substitute(PERSON_NAME=name.title())

        # Prints out the message body in the terminal
        print(message)

        # Setup the parameters of the message
        msg['From']=smtp_email
        msg['To']=email
        msg['Subject']="This is a TEST"

        # Add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # Send the message via the server set up earlier
        s.send_message(msg)
        del msg

    # Terminate the SMTP session and close the connection
    s.quit()

"""
Valid start time and end time must be in EEN format.  

All times in the EEN system use the UTC timezone.

For example, November 21, 2018 01:23:45 AM would translate to 20181121012345.000

The last 3 digits are for microseconds and are required.
"""

# Required datetime variables
now = datetime.datetime.now()
yesterday = now - datetime.timedelta(days = 1)
yesterday_friendly = yesterday.strftime("%m/%d/%Y")
start_time = yesterday.strftime("%Y%m%d")
end_time = yesterday.strftime("%Y%m%d")

print(now.strftime("%Y-%m-%d %H:%M:%S"))
print("Cooper Surgical - camera footage archives")
print("Starting process...")

# Print statements used for testing purposes only, can be removed once in production
"""
print("now = %s" % (now))
print("yesterday = %s" % (yesterday))
print("start_time = %s" % (start_time))
print("end_time = %s" % (end_time))
print("above variables used for testing purposes only.")
"""

###
# UNCOMMENT BELOW SECTION AND REPLACE TESTING SECTION WHEN IN PRODUCTION
###

# start_timestamp and end_timestamp below are values to be used in production - 24 hour fetch period
"""
noon_start = "120000.000"
noon_end = "115959.999"

start_timestamp = start_time + noon_start
end_timestamp =   end_time + noon_end
noon_end_friendly = "12:00 UTC"
end_noon_friendly = "11:59 UTC"
start_friendly = ("%s %s" % (yesterday_friendly, noon_friendly))
end_friendly = ("%s %s" % (yesterday_friendly, noon_end_friendly))

if start_timestamp == "" or end_timestamp == "":
    print("Please put in a start and ending time")
    sys.exit()

print("Fetching video files captured between %s and %s..." % (start_friendly, end_friendly))
"""
###
# END PRODUCTION SECTION
###

###
# THIS SECTION TO BE USED FOR TESTING PURPOSES ONLY
###

test_start = "120000.000"
test_end = "130000.000"
test_start_friendly = "12:00 UTC"
test_end_friendly = "13:00 UTC" 

start_timestamp = start_time + test_start
end_timestamp = end_time + test_end

if start_timestamp == "" or end_timestamp == "":
    print("Please put in a start and ending time")
    sys.exit()

print("Fetching video files captured on %s between %s and %s" % (yesterday_friendly, test_start_friendly, test_end_friendly))

###
# END TESTING SECTION - COMMENT/REMOVE THIS ENTIRE SECTION WHEN IN PRODUCTION
###

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

# filter by camera ID
camera_id_list = [i[1] for i in device_list if i[3] == 'camera']

# filter by friendly camera name
friendly_id_list = [i[2] for i in device_list if i[3] == 'camera']

# create merged list with camera ID and friendly camera name
merged_camera_list = [i+'_'+j for i,j in zip(camera_id_list,friendly_id_list)]
''.join(merged_camera_list)
print(merged_camera_list)

# count of cameras found in the environment
camera_list_len = len(camera_id_list)
print("Found %s cameras..." % camera_list_len)

# Check if directory exists to save video files
def check_directory_create(current_wd,start_time):
    archive_dir = os.path.abspath("\%s-archive" % (start_time))
    if os.path.exists(archive_dir):
        os.mkdir(archive_dir)
        print("Creating new directory %s to save files downloaded from today." % (archive_dir))
        return archive_dir
    else:
        print("Directory %s already exists... files downloaded today will be saved to this directory." % (archive_dir))
        return archive_dir

check_directory_create(current_wd, start_time)

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

print("Step 4: Gathering list of videos to download for each camera...")

session_list = {}
session_list_large = {}

download_path = check_directory_create(current_wd,start_time)

# Create text file that lists the camera_ids with videos to download for this session, and the number of video files available to download.
def session_download_list(start_time, camera_id, video_list):
    video_list_len = len(video_list)
    if video_list_len >= 1:
        add_to_file = "%s: found %s video files to download during this session/n" % (camera_id, video_list_len)
        with open ("download_list_%s.txt" % (start_time), "w") as file:
            file.writelines(add_to_file)
    
    # elif video_list_len == 1:
        # add_to_file = "%s: found %s video files to download during this session/n" % (camera_id, video_list_len)
        # with open ("download_list_%s.txt" % (start_time), "w") as file:
            # file.writelines(add_to_file)
        # with open ("large_file_download_list_%s.txt" % (start_time), "w") as file:
            # file.writelines("%s: %s/n" % video_list)
    else:
        print("skipping %s... no files to download" % camera_id)

for camera_id in camera_id_list:
    video_list = get_video_list(camera_id)
    video_list_len = len(video_list)
    if video_list_len > 1:
        print("Found %s videos to download for camera %s" % (video_list_len, camera_id))
        session_list[camera_id] = video_list
    elif video_list_len == 1:
        print("Found a large video file for camera %s... Skipping for now and will download at the end." % (camera_id))
        with open("large_video_list.txt", "w") as file:
            large_file_log = json.dumps(video_list)
            file.write("%s/n" % large_file_log)
        session_list_large[camera_id] = video_list
    else:
        print("No videos found for camera %s. Skipping..." % camera_id)

camera_ids_with_files = len(session_list)
print("%s of %s cameras have video files ready to download." % (camera_ids_with_files, camera_list_len))

###
# Use functions below to create required directories and files
###

# Create file containing list of devices in the environment
"""
def save_device_list_to_file(merged_camera_list,start_time):
    with open("device_list_%s.txt" % (start_time), "w") as file:
        file.write(json.dumps(merged_camera_list))
    print("device_list_%s.txt has been saved to file." % (start_time))

save_device_list_to_file(merged_camera_list=merged_camera_list,start_time=start_time)
"""

# Save video_list from get_video_list() to .txt file
"""
def save_video_list_to_file(video_list):
    with open("video_list", "w") as file:
        file.write(json.dumps(video_list))
    print("video_list saved as new file: 'video_list'.")

save_video_list_to_file(get_video_list(camera_id=""))
"""

# Recall video_list stored in .txt file
"""
def load_video_list_from_file(camera_id):
    with open(camera_id, "w") as file:
        video_list_read = file.read(json.loads(camera_id))
    return video_list_read

load_video_list_from_file(camera_id="")
"""

###
# Step 5: Download the files from the video_list to the local directory
###

###
# Step 5a. TEST: Download and send files to Cooper S3 bucket
###

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

        response = session.request("GET", url, data=payload, params=querystring, headers=headers)
        print(HTTP_STATUS_CODE[response.status_code])

        if response.status_code == 200:
            local_filename = "%s-%s.flv" % (camera_id, video_list[current_video]['e'])
            local_path = ("%s\%s" % (output_dir, local_filename))
            current_video += 1
            
            with open(local_path, "wb") as f:
                total_length = int(response.headers.get('content-length'))
                for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                    else:
                        print("error downloading last file...")
                        continue
            if upload_to_aws(local_path,bucket=local_settings.bucket) == True:
                print("%s has been uploaded to the S3 bucket successfully" % local_filename)
        else:
            print("HTTP Status Code: %s" % HTTP_STATUS_CODE[response.status_code])
            continue
    else:
        print("Finished downloading videos for camera_id %s ..." % camera_id)

print("Step 5: Download video files to working directory")

for key in session_list:
    print("Initializing download of %s video files for camera %s" % (len(session_list[key]), key))
    download_videos(download_path, key, session_list[key])



###
# Trigger email notifications and activity summary here...
###

# Test email notification used as temporary placeholder
if __name__ == '__main__':
    main()

print("Email notification service initiated...")
print("All emails have been sent successfully.")

print("Downloads complete - exiting process...")
sys.exit()

