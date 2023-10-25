import json
import requests
import drive
import math
import sheets
import os

def get_all_calls():

    url = "https://us-13358.api.gong.io/v2/calls/extensive"

    payload = {
        "filter": {},
        "contentSelector": {
            "context": "None",
            "exposedFields": {
                "parties": True,
                "content": {
                    "structure": False,
                    "topics": False,
                    "trackers": False,
                    "trackerOccurrences": False,
                    "pointsOfInterest": False
                },
                "interaction": {
                    "speakers": True,
                    "video": True,
                    "personInteractionStats": True,
                    "questions": True
                },
                "collaboration": {"publicComments": True},
                "media": True
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic SEtJV0RQVExMTUlXU1NPS1dKVldOWFJQTk1LNTJQREk6ZXlKaGJHY2lPaUpJVXpJMU5pSjkuZXlKbGVIQWlPakl3TVRFM056azBOallzSW1GalkyVnpjMHRsZVNJNklraExTVmRFVUZSTVRFMUpWMU5UVDB0WFNsWlhUbGhTVUU1TlN6VXlVRVJKSW4wLktITnlwdm9EVDBzd0dQUmtRMkM2V2IwVzZIQjI2SHBlSEp1U1pZLUMyckE="
    }

    all_calls = []

    page_num = 0

    current_page = 0

    call_counter = 0

    while True:

        response = requests.request("POST", url, json=payload, headers=headers)

        if response.status_code == 200:

            data = response.json()

            if page_num == 0:

                page_num = math.floor(data["records"]["totalRecords"] / data["records"]["currentPageSize"])

                print(f"TOTAL PAGES: {page_num}")

            current_page = data["records"]["currentPageNumber"]

            try:

                cursor = data["records"]["cursor"]

            except KeyError:

                cursor = None

            print(f"\nCURRENT PAGE: {current_page}")

            for call in data['calls']:

                if call_counter < 1033:

                    call_counter += 1

                    continue

                else:

                    all_calls.append(call)

                    call_counter += 1

            if page_num == current_page:

                print("Finish exporting calls to JSON.")

                break

            current_page += 1

            payload["cursor"] = cursor

            print("SUCCESS\n")

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
    else:
        print(f"Failed to download video. Status code: {response.status_code}")

def parse_all_calls(calls):

    for i,call in enumerate(calls):

        if i < 1032:

            continue

        try:
            id = call["metaData"]["id"]
        except KeyError:
            id = ""

        try:
            title = call["metaData"]["title"].replace("/", "-").replace("\\", "-").replace("<", "-").replace(">", "-").replace("|", "-")
        except KeyError:
            title = ""

        try:
            duration = call["metaData"]["duration"]
        except KeyError:
            duration = 0

        try:
            started = call["metaData"]["started"]
        except KeyError:
            started = ""

        try:

            atts = []

            for att in call["parties"]:

                try:

                    name = att['name']

                except Exception:

                    name = ""

                try:

                    email = att['emailAddress']

                except Exception:

                    email = ""

                atts.append(f"{name} ({email})")

            attendees = ", ".join(atts)

        except KeyError:
            attendees = ""

        try:
            video_url = call["media"]["videoUrl"]
        except KeyError:
            video_url = ""

        try:        
            audio_url = call["media"]["audioUrl"]
        except KeyError:
            audio_url = ""

        print(F"{video_url}")
        print(F"{audio_url}")

        if title and video_url:

            download_video(video_url, title)

            drive_url = drive.upload(f"{title}.mp4")

            os.remove(f"{title}.mp4")

        elif title and audio_url:

            download_video(audio_url, title)

            drive_url = drive.upload(f"{title}.mp4")

            os.remove(f"{title}.mp4")

        else:

            with open("Error_videos.txt", "a") as f:

                line = f"video {i}, title {title if title else 'No title'}\n"

                f.write(line)

            drive_url = ""

        sheets.insert_to_sheet([id, title, attendees, started, duration, drive_url])

        print(f"[{i}] Successfuly uploaded/processed video: {title}")


if __name__ == "__main__":

    with open("all_calls.json", "w") as op:

        json.dump(get_all_calls(), op, indent=4)
    
    # with open("all_calls.json", "r") as op:

    #     all_calls = json.load(op)

    #     parse_all_calls(all_calls)