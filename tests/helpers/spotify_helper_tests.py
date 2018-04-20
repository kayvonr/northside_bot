import unittest

from helpers import spotify_helper


class SpotifyHelperTest(unittest.TestCase):

    def test_finding_spotify_urls(self):
        # mix of links that should pass and links that should be ignored
        messages = (
            ("hello there https://open.spotify.com/album/5mv7rhnCcP3BUYP1jTA6Z4?si=6kn5L4sTSPu1P5iIjFVt3Q foo", False),
            ("boom roasted again https://open.spotify.com/track/4NmTNaaY7IlT8qTZ2GModd?si=_QGz04SNSzasIg1Vf2rxuQ. something", True),
            ("https://open.spotify.com/artist/2DaP4uXwKOXAaD77XokW9a?si=oBCpo4HHRniPJ7-kgujjpQ, another one", False),
            ("Here is a spotify link: https://open.spotify.com/user/kayvon2/playlist/6ppEt95jwo4N2sJSQIaFHS?si=IBn-F1SoTw2GgX2kknMidA", False)
        )

        for message, should_pass in messages:
            res = spotify_helper.extract_spotify_urls(message)
            self.assertEqual(bool(res), should_pass, "{} failed (supposed to be {})".format(message, should_pass))

        # all links that should pass
        messages = (
            "https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g",
            "Yo: https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g",
            "here's a song https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g",
            "https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g something else here",
            "beginning https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g and end",
            "link https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g, with punctuation",
            "https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ?si=SBd5WRanQuy4brwa-WCb4g. what about a period",
        )

        for message in messages:
            self.assertEqual(spotify_helper.extract_spotify_urls(message)[0], "https://open.spotify.com/track/1Yf8RtP4KpjyoEuTyJkMDZ")
