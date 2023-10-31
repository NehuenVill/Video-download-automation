from io import BytesIO
import json
from time import sleep
import requests
import drive
import math
import sheets
import os
import concurrent.futures
import threading
import random
import random
import string

def generate_random_string(length=6):
    """
    Generate a random string of the specified length.

    Args:
        length (int): The length of the random string.

    Returns:
        str: The random string.
    """
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

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

                # if call_counter < 1033:

                #     # call_counter += 1

                #     # continue

                #     pass

                # else:

                all_calls.append(call)

                # call_counter += 1

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

        if os.path.exists("videos/"+filename+".mp4"):

            filename = filename+"_"+generate_random_string()+".mp4"

            with open("videos/"+filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            return filename
    
        else:

            with open("videos/"+filename+".mp4", 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)

            return None

    else:
        print(f"Failed to download video. Status code: {response.status_code}")

        return None


def download_and_reduce_quality(url, target_bitrate, filename):
    r = requests.get(url, stream=True)

    if r.status_code == 200:

        with open(filename, 'wb') as f:
            f.write(r.content)

        clip = VideoFileClip(filename)
        
        # Calculate the target bitrate based on the original video's bitrate
        original_bitrate = clip.fps * clip.size[0] * clip.size[1]
        reduction_factor = target_bitrate / original_bitrate
        resized_clip = clip.resize(0.5)  # Reduce resolution by half
        resized_clip.write_videofile(filename, codec='libx264', bitrate= f"{target_bitrate}k")

        print("Done successfully")

    else:
        print("Failed to download the video")


def process_call(i, call):

    try:

        try:
            id = call["metaData"]["id"]
        except KeyError:
            id = ""

        try:
            title = call["metaData"]["title"].replace("/", "-").replace("\\", "-").replace("<", "-").replace(">", "-").replace("|", "-")\
                .replace("@","-").replace(":",".").replace("\"","").replace("?","").replace("*", "")
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

        if title and video_url:

            filename = download_video(video_url, title)

            if filename:

                title = filename.replace(".mp4", "")

            drive_url = drive.upload(f"{title}.mp4")

            os.remove(f"videos/{title}.mp4")

        elif title and audio_url:

            filename = download_video(audio_url, title)   

            if filename:

                title = filename.replace(".mp4", "")

            drive_url = drive.upload(f"{title}.mp4")

            os.remove(f"videos/{title}.mp4")

        else:

            with open("Error_videos.txt", "a") as f:

                line = f"video {i}, title {title if title else 'No title'}\n"

                f.write(line)

            drive_url = ""

        sheets.insert_to_sheet([id, title, attendees, started, duration, drive_url])

        print(f"[{i}] Successfuly uploaded/processed video: {title}")

        # return {"id":id,
        #         "title": title,
        #         "attendees": attendees,
        #         "started": started,
        #         "duration": duration,
        #         "file": f"{title}.mp4"}

    except Exception as e:

        print(f"[{i}] Error occurred: {e}")

        with open("Error_videos.txt", "a") as f:

            line = f"video {i}, title {title if title else 'No title'}, e: {e}\n"

            f.write(line)

def process_call_local(i, call):

    try:

        try:
            id = call["id"]
        except KeyError:
            id = ""

        try:
            title = call["title"].replace("/", "-").replace("\\", "-").replace("<", "-").replace(">", "-").replace("|", "-")\
                .replace("@","-").replace(":",".").replace("\"","").replace("?","").replace("*", "")
        except KeyError:
            title = ""

        try:
            duration = call["duration"]
        except KeyError:
            duration = 0

        try:
            started = call["started"]
        except KeyError:
            started = ""

        try:

            attendees = call["attendees"]

        except KeyError:
            attendees = ""

        file = call["file"]

        drive_url = drive.upload(file)

        os.remove(f"videos/{file}")

        sheets.insert_to_sheet([id, title, attendees, started, duration, drive_url])

        print(f"[{i}] Successfuly uploaded/processed video: {title}")

    except Exception as e:

        print(f"[{i}] Error occurred: {e}")

        with open("Error_videos_2.txt", "a") as f:

            line = f"video {i}, title {title if title else 'No title'}, e: {e}\n"

            f.write(line)


max_threads = 20

barrier = threading.Barrier(parties=max_threads)

def process_batch(batch):

    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(process_call_local, element[0], element[1]) for element in batch]
        concurrent.futures.wait(futures)

    # all_data = []

    # with open("local_calls_final.json", "r") as f:

    #     loaded_data = json.load(f)

    #     for video in loaded_data:

    #         all_data.append(video)

    # for future in futures:

    #     all_data.append(future.result())

    # with open("local_calls_final.json", "w") as f:

    #     json.dump(all_data, f, indent=4)


def parse_all_calls(calls):

    # numbers = [2851, 2856, 2855, 2857, 3074, 3082, 3127, 3136, 3176, 3171, 3373, 3377, 3375, 3372, 3466, 3516, 3527, 3523, 3534, 3598, 3611, 3617, 3624, 3627, 3644, 3646, 3647, 3724, 3722, 3732, 3783, 3941, 3940, 3955, 3993, 3984, 4116, 4119, 4131, 4154, 4155, 4151, 4184, 4175, 4215, 4216, 4227, 4222, 4242, 4264, 4275, 4277, 4294, 4373, 4384, 4428, 4433, 4541, 4545, 4587, 4614, 4630, 4671, 4673, 4680, 4708, 4702, 4764, 4798, 4793, 4814, 4822, 4828, 4851, 4854, 4891, 5099, 5110, 5109, 5126, 5141, 5179, 5187, 5216, 5238, 5247, 5266, 5282, 5301, 5354, 5357, 5362, 5383, 5398, 5508, 5566, 5558, 5572, 5667, 6411, 6434, 6717, 6765, 7053, 7200, 7318, 8683, 8796, 8909, 8926, 8979, 9249, 9360, 9363, 9375, 10101, 10371, 10412, 10410, 10445, 10440, 10442, 10431, 10444, 10428, 10429, 10441, 10430, 10439, 10436, 10447, 10438, 10435, 10446, 10437, 10433, 10434, 10443, 10432, 10454, 10452, 10460, 10448, 10453, 10467, 10465, 10455, 10466, 10451, 10457, 10463, 10461, 10450, 10449, 10458, 10456, 10462, 10459, 10464, 11884, 11946, 12232, 10101]

    # calls = [calls[num+1033] for num in numbers]

    for i in range(0, len(calls), max_threads):
        chunk = calls[i:i+max_threads]

        calls_20 = [] 

        for j, _call in enumerate(chunk):

            calls_20.append((i+j, _call))

        process_batch(calls_20)

def filter_and_write_calls(json_data, specific_ids):
    """
    Filter JSON data based on specific IDs and write it to "calls_2.json."

    Args:
        json_data (list): List of JSON objects.
        specific_ids (list): List of specific IDs to filter.

    Returns:
        None
    """
    filtered_data = [entry for entry in json_data if entry["metaData"]["id"] in specific_ids]

    # Write the filtered data to "calls_2.json"
    with open("calls_2.json", "w") as outfile:
        json.dump(filtered_data, outfile, indent=4)


def find_duplicate_titles(json_data):
    """
    Find the IDs of elements with duplicate titles in the JSON data.

    Args:
        json_data (list): List of JSON objects.

    Returns:
        list: List of IDs with duplicate titles.
    """
    # Create a dictionary to count the occurrences of each title
    title_count = {}
    
    # Initialize a list to store IDs with duplicate titles
    duplicate_ids = []
    
    # Iterate through the JSON data
    for entry in json_data:

        if entry == None:

            continue

        title = entry["title"]
        call_id = entry["id"]
        
        # Count the occurrences of each title
        title_count[title] = title_count.get(title, 0) + 1
        
        # If a title has occurred more than once, add the ID to the list of duplicates
        if title_count[title] > 1:
            duplicate_ids.append(call_id)
    
    return duplicate_ids

def extract_titles(data):
    titles = [entry["metaData"]['title'] for entry in data]
    return titles

# Function to find the first element with a specific title in another JSON file
def find_element_by_title(data, title):

    for entry in data:
        if entry['metaData']['title'] == title:
            return entry
    return None

def delete_items_by_ids(file_in, ids_to_exclude, output_json_file):
    """
    Delete items from a JSON file based on a list of IDs to exclude and save the result to a new JSON file.

    Args:
        input_json_file (str): The input JSON file to read.
        ids_to_exclude (list): List of IDs to exclude.
        output_json_file (str): The output JSON file to save the filtered data.

    Returns:
        None
    """

    filtered_data = [entry for entry in file_in if entry["metaData"]['id'] not in ids_to_exclude]

    with open(output_json_file, 'w') as file:
        json.dump(filtered_data, file, indent=4)


if __name__ == "__main__":

    # with open("all_calls_2.json", "r") as op:

    #     inp = json.load(op)

    # #     list_ids = find_duplicate_titles(inp["videos"])

    # #     print(len(list_ids))

    # #     delete_items_by_ids(inp, list_ids, "local_calls_final.json")

    #     id_list = sheets.get_all_ids()

    #     delete_items_by_ids(inp,id_list, "calls_left_after_cleaning.json")

    # with open("all_calls_2.json", "r") as op:

    #     op = json.load(op)

        # filter_and_write_calls(op, list_ids)

    # with open('calls_2.json', "r") as op:

    #     op = json.load(op)

    #     titles = extract_titles(op)

    #     entries = [entry for entry in op]

    # with open("all_calls_2.json", "r") as op:

    #     op = json.load(op)

    #     for title in titles:

    #         element = find_element_by_title(op, title)

    #         entries.append(element)

    # with open("calls_3.json", "w") as op:

    #     json.dump(entries, op, indent=4)

    # with open("all_calls_2.json", "w") as op:

    #     json.dump(get_all_calls(), op, indent=4)
    
    with open("calls_local_data.json", "r") as op:

        all_calls = json.load(op)["videos"]

        parse_all_calls(all_calls)

    # with open("all_calls_2.json", "r") as op:

    #     all_calls = json.load(op)

    #     parse_all_calls(all_calls)