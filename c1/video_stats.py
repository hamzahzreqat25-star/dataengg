import requests
import json
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
API_KEY = os.getenv("API_KEY")
forHandle = "MrBeast"
maxResults = 50


def get_playlist_id():
    url = (
        f"https://youtube.googleapis.com/youtube/v3/channels"
        f"?part=contentDetails&forHandle={forHandle}&key={API_KEY}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    items = data.get("items", [])
    if not items:
        raise ValueError("No channel found for handle")

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_video_id(playlist):
    video_ids = []
    pageToken = None
    base_url = (
        f"https://youtube.googleapis.com/youtube/v3/playlistItems"
        f"?part=contentDetails&maxResults={maxResults}&playlistId={playlist}&key={API_KEY}"
    )

    while True:
        url = base_url + (f"&pageToken={pageToken}" if pageToken else "")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        pageToken = data.get("nextPageToken")
        if not pageToken:
            break

    return video_ids


def extract_video_data(video_ids):
    extracted_data = []

    def batch_list(video_id_list, batch_size):
        for i in range(0, len(video_id_list), batch_size):
            yield video_id_list[i : i + batch_size]

    for batch in batch_list(video_ids, maxResults):
        video_ids_str = ",".join(batch)
        url = (
            f"https://youtube.googleapis.com/youtube/v3/videos"
            f"?part=contentDetails,snippet,statistics&id={video_ids_str}&key={API_KEY}"
        )

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            snippet = item["snippet"]
            contentDetails = item["contentDetails"]
            statistics = item.get("statistics", {})

            extracted_data.append(
                {
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "publishedAt": snippet["publishedAt"],
                    "duration": contentDetails["duration"],
                    "viewCount": statistics.get("viewCount"),
                    "likeCount": statistics.get("likeCount"),
                    "commentCount": statistics.get("commentCount"),
                }
            )

    return extracted_data


def save_to_json(extract_data):
    os.makedirs("./data", exist_ok=True)
    file_path = f"./data/c1_data_{date.today()}.json"
    with open(file_path, "w", encoding="utf-8") as json_outfile:
        json.dump(extract_data, json_outfile, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    playlist = get_playlist_id()
    video_ids = get_video_id(playlist)
    extract_data = extract_video_data(video_ids)
    save_to_json(extract_data)