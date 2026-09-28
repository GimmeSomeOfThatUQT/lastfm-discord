import requests
import time
from pypresence import Presence, ActivityType
import os
from dotenv import load_dotenv

load_dotenv("secrets.env")

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")

CHECK_INTERVAL = 10


def get_now_playing():
    url = "https://ws.audioscrobbler.com/2.0/"

    params = {
        "method": "user.getRecentTracks",
        "user": LASTFM_USERNAME,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        tracks = data.get("recenttracks", {}).get("track", [])

        if not tracks:
            return None

        track = tracks[0]

        # Only show something while currently playing
        now_playing = (
            "@attr" in track
            and track["@attr"].get("nowplaying") == "true"
        )

        if not now_playing:
            return None

        artist = track.get("artist", {}).get("#text", "Unknown Artist")
        title = track.get("name", "Unknown Track")
        album = track.get("album", {}).get("#text", "")

        # Get album artwork
        album_art = ""

        images = track.get("image", [])

        # Prefer the largest Last.fm image
        for image in images:
            if image.get("size") == "extralarge":
                if image.get("#text"):
                    album_art = image["#text"]
                    break

        # Fallback to any available image
        if not album_art:
            for image in reversed(images):
                if image.get("#text"):
                    album_art = image["#text"]
                    break

        return {
            "artist": artist,
            "title": title,
            "album": album,
            "album_art": album_art,
        }

    except Exception as e:
        print(f"Last.fm error: {e}")
        return None


rpc = Presence(DISCORD_CLIENT_ID)

print("Connecting to Discord...")

try:
    rpc.connect()
    print("Connected to Discord!")
except Exception as e:
    print(f"Could not connect to Discord: {e}")
    raise


last_track = None

try:
    while True:

        track = get_now_playing()

        if track != last_track:

            if track:

                print()
                print(f"Artist: {track['artist']}")
                print(f"Track:  {track['title']}")
                print(f"Album:  {track['album']}")
                print(f"Art:    {track['album_art']}")
                print("Playing: True")

                rpc.update(
                    activity_type=ActivityType.LISTENING,
                    details=track["title"],
                    state=track["artist"],
                    large_image=track["album_art"],
                    large_text=track["album"],
                )

            else:

                print()
                print("Nothing currently playing.")

                rpc.clear()

            last_track = track

        time.sleep(CHECK_INTERVAL)


except KeyboardInterrupt:

    print("\nStopping...")

    try:
        rpc.clear()
        rpc.close()
    except Exception:
        pass
