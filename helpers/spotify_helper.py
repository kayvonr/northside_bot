import re


TRACK_URL_PATTERN = re.compile("(?P<spotify_url>https?://open\.spotify\.com/track/[a-zA-Z0-9]+)")


def extract_spotify_urls(message):
    return TRACK_URL_PATTERN.findall(message)


def add_track_to_playlist(url, playlist_id):
    pass
