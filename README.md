# CooperGenomics
Python scripting to fetch and store camera footage to a local server for archiving

# getVideoDownload_production.py
This is the main python script that will run the fetch/download process. Credentials required to call the API can be found in the local_settings.py file.

# local_settings.py
contains username/password and API key needed to run the script. Credentials will need to be updated when the script is placed into production

# Script Basics

1. Checks if EagleEye username / password and API-key are present. If not present, script terminates.

2. 'start_time' and 'end-time' are required for the script to run. the time used for these variables will determine the period the script will attempt to pull video files for. These values should be configured alongside the running schedule for the script to ensure all video files are retrieved on a running basis.

3. Step 1 and 2 - Logs into the EagleEye API environment and creates a session to use while retrieving the files. HTTP response codes are returned via the terminal, 'OK' confirms login successful.

4. Step 3 - Scans for devices within the environment authorized to the user. Will return device list and details related to each device. Individual cameras identified by 'camera_id' from this point moving forward.

5. Step 4 - get video lists. Iterates through each of the cameras and IDs video files to be downloaded for the given time period.

6. Step 5 - download videos. For each camera and video list, video file is downloaded to the working directory if HTTP Status Code 200 is returned. video file is .flv extension and naming convention is 'camera_id'-'end-timestamp'[video_list].flv

7. If any other HTTP Status Code is returned (error, etc.) the error is noted in the log and continues to the next file to download.

# Additional Functionality
1. Add additional logging - create a file with list of camera_ids, video_files, etc. Create a log of files that aren't able to download due to HTTP Response Code Error

2. Notifications - create notification service, email XX user when script has:
    1. Started / failed to start
    2. Completed / interrupted before completing
    3. Summary - # videos tried/succesful download
    4. Broad summary - snapshot of the script running every week, etc.

3. Exception handling - when exceptions occur, handle automatically:
    1. Restart if script fails/interrupted - check if video file already downloaded / pick up where left off
    2. Retry downloading video files that failed to download