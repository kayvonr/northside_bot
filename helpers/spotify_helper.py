import re
from operator import itemgetter


TRACK_URL_PATTERN = re.compile("(?P<full_url>https?://open\.spotify\.com/track/(?P<track_id>[a-zA-Z0-9]+))")


def extract_spotify_track_ids(message):
    return map(
        itemgetter(1),
        TRACK_URL_PATTERN.findall(message)
    )


def add_track_to_playlist(track_id, playlist_id):
    pass
