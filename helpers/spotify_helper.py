import re
from operator import itemgetter
import requests

from spotipy.util import prompt_for_user_token
from link import lnk

import conf


TRACK_URL_PATTERN = re.compile("(?P<full_url>https?://open\.spotify\.com/track/(?P<track_id>[a-zA-Z0-9]+))")
ALBUM_URL_PATTERN = re.compile("(?P<full_url>https?://open\.spotify\.com/album/(?P<album_id>[a-zA-Z0-9]+))")
DISCOVER_URL_PATTERN = re.compile("(?P<full_url>https?://open\.spotify\.com/user/spotify/playlist/(?P<playlist_id>[a-zA-Z0-9]+))")

msg = lnk.msg


def has_track_link(message):
    return _string_contains_pattern(message, TRACK_URL_PATTERN)


def has_album_link(message):
    return _string_contains_pattern(message, ALBUM_URL_PATTERN)


def _string_contains_pattern(message, pattern):
    return pattern.search(message) is not None


def extract_spotify_track_ids(message):
    return _extract_ids(message, TRACK_URL_PATTERN)


def extract_spotify_album_ids(message):
    return _extract_ids(message, ALBUM_URL_PATTERN)


def extract_spotify_discover_id(message):
    return _extract_ids(message, DISCOVER_URL_PATTERN)


def _extract_ids(message, pattern):
    return map(
        itemgetter(1),
        pattern.findall(message)
    )


def _build_spotify_uri(track_id):
    return "spotify:track:{}".format(track_id)


def _get_auth_token():
    return prompt_for_user_token(
        conf.NORTHSIDE_SPOTIFY_USER_ID,
        conf.SPOTIFY_SCOPE_NEEDED
    )


def add_album_to_playlist(album_id, playlist_id):
    resp = get_tracks_in_album(album_id)
    # ugh, shitty. sorry.
    if isinstance(resp, tuple):
        return resp

    track_ids = resp
    return add_tracks_to_playlist(track_ids, playlist_id)


def get_tracks_in_album(album_id):
    token = _get_auth_token()

    headers = {"Authorization": "Bearer {}".format(token)}
    url = conf.SPOTIFY_ALBUMS_API_URL.format(album_id=album_id) + "?limit=50"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        msg.warn("Error getting track IDs for album: {}".format(resp.json()))
        return False, resp

    return [r['id'] for r in resp.json()['items']]


def add_discover_to_playlist(discover_playlist_id, playlist_id):
    return add_playlist_to_playlist(conf.SPOTIFY_SYSTEM_USER_ID, discover_playlist_id, playlist_id)


def add_playlist_to_playlist(user_id, og_playlist_id, playlist_id):
    resp = get_tracks_in_playlist(user_id, og_playlist_id)
    # ugh, shitty. sorry.
    if isinstance(resp, tuple):
        return resp

    track_ids = resp
    return add_tracks_to_playlist(track_ids, playlist_id)


def get_tracks_in_playlist(user_id, playlist_id):
    token = _get_auth_token()

    headers = {"Authorization": "Bearer {}".format(token)}
    url = conf.SPOTIFY_PLAYLIST_API_URL.format(user_id=user_id, playlist_id=playlist_id)

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        msg.warn("Error getting track IDs for playlist: {}".format(resp.json()))
        return False, resp

    return [track['track']['id'] for track in resp.json()['items']]


def add_track_to_playlist(track_id, playlist_id):
    return add_tracks_to_playlist([track_id], playlist_id)


def add_tracks_to_playlist(track_ids, playlist_id):
    token = _get_auth_token()

    headers = {"Authorization": "Bearer {}".format(token)}
    url = conf.SPOTIFY_ADD_TRACK_API_URL.format(
        user_id=conf.NORTHSIDE_SPOTIFY_USER_ID,
        playlist_id=playlist_id,
    )

    body = {"uris": [_build_spotify_uri(t_id) for t_id in track_ids]}

    msg.debug("Adding track, url: {}, body: {}".format(url, body))

    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code < 200 or resp.status_code >= 300:
        msg.warn("Unsuccessful add track call: {}".format(resp.json()))
        return False, resp

    return True, resp

