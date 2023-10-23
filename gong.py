import requests
import drive
import math
import sheets

def get_all_calls(url, params, headers):


    all_calls = []

    page_num = 0

    current_page = 0

    while True:

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:

            data = response.json()
            print(data)

            if page_num == 0:

                page_num = math.floor(data["totalRecords"] / data["currentPageSize"])

            current_page = data["currentPageNumber"]

            cursor = data["cursor"]

            for call in data['calls']:

                all_calls.append(call)

            if page_num == current_page:

                break

        else:

            print("There's been a problem with the request")

    return all_calls

def download_video(url, filename):

    response = requests.get(url, stream=True)
       # Check if the request was successful
    if response.status_code == 200:
        # Write the content to a file
        with open(filename+".mp4", 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Video downloaded successfully as {filename}")
    else:
        print(f"Failed to download video. Status code: {response.status_code}")

def parse_all_calls(calls):

    for call in calls:

        id = call["metaData"]["id"]
        title = call["metaData"]["title"]
        duration = call["metaData"]["duration"]
        started = call["metaData"]["started"]

        attendees = None

        video_url = call["metaData"]["videoUrl"]

        download_video(video_url, title)

        drive_url = drive.upload(f"{title}.mp4")

        sheets.insert_to_sheet([id, title, attendees, started, duration, drive_url])

        


        

    