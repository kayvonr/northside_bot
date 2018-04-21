import re
from operator import itemgetter
import requests

from spotipy.util import prompt_for_user_token
from link import lnk

import conf


TRACK_URL_PATTERN = re.compile("(?P<full_url>https?://open\.spotify\.com/track/(?P<track_id>[a-zA-Z0-9]+))")

msg = lnk.msg


def extract_spotify_track_ids(message):
    return map(
        itemgetter(1),
        TRACK_URL_PATTERN.findall(message)
    )


def _build_spotify_uri(track_id):
    return "spotify:track:{}".format(track_id)


def _get_auth_token():
    return prompt_for_user_token(
        conf.SPOTIFY_USER_ID,
        conf.SPOTIFY_SCOPE_NEEDED
    )


def add_track_to_playlist(track_id, playlist_id):
    token = _get_auth_token()

    headers = {"Authorization": "Bearer {}".format(token)}
    url = conf.SPOTIFY_ADD_TRACK_API_URL.format(
        user_id=conf.SPOTIFY_USER_ID,
        playlist_id=conf.SPOTIFY_TRACK_PLAYLIST_ID,
        track_id=_build_spotify_uri(track_id)
    )

    msg.info("Adding track, url: {}".format(url))

    resp = requests.post(url, headers=headers)
    if resp.status_code < 200 or resp.status_code >= 300:
        msg.warn("Unsuccessful add track call: {}".format(resp.json()))
        return False, resp

    return True, resp
