# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
"""
import os
import message
import time

from slackclient import SlackClient
from link import lnk

from helpers import spotify_helper
import conf

# To remember which teams have authorized your app and what tokens are
# associated with each team, we can store this information in memory on
# as a global object. When your bot is out of development, it's best to
# save this in a more persistant memory store.
authed_teams = {}

msg = lnk.msg


class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = "mymom"
        self.emoji = ":pill:"
        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        self.oauth = {"client_id": os.environ.get("CLIENT_ID"),
                      "client_secret": os.environ.get("CLIENT_SECRET"),
                      # Scopes provide and limit permissions to what our app
                      # can access. It's important to use the most restricted
                      # scope that your app will need.
                      "scope": "bot"}
        self.verification = os.environ.get("VERIFICATION_TOKEN")

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
        # self.client = SlackClient("")
        self.client = SlackClient(os.environ.get("BOT_TOKEN"))
        # We'll use this dictionary to store the state of each message object.
        # In a production envrionment you'll likely want to store this more
        # persistantly in  a database.
        self.messages = {}

    def auth(self, code):
        """
        Authenticate with OAuth and assign correct scopes.
        Save a dictionary of authed team information in memory on the bot
        object.

        Parameters
        ----------
        code : str
            temporary authorization code sent by Slack to be exchanged for an
            OAuth token

        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpoint
        auth_response = self.client.api_call(
                                "oauth.access",
                                client_id=self.oauth["client_id"],
                                client_secret=self.oauth["client_secret"],
                                code=code
                                )

        print("(DEBUG) Bot auth response: {}".format(auth_response))

        # To keep track of authorized teams and their associated OAuth tokens,
        # we will save the team ID and bot tokens to the global
        # authed_teams object
        authed_teams = {"bot_token": auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's
        # bot token
        self.client = SlackClient(authed_teams["bot_token"])

    def open_dm(self, user_id):
        """
        Open a DM to send a welcome message when a 'team_join' event is
        recieved from Slack.

        Parameters
        ----------
        user_id : str
            id of the Slack user associated with the 'team_join' event

        Returns
        ----------
        dm_id : str
            id of the DM channel opened by this method
        """
        new_dm = self.client.api_call("im.open",
                                      user=user_id)
        dm_id = new_dm["channel"]["id"]
        return dm_id

    def onboarding_message(self, team_id, user_id):
        """
        Create and send an onboarding welcome message to new users. Save the
        time stamp of this message on the message object for updating in the
        future.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # We've imported a Message class from `message.py` that we can use
        # to create message objects for each onboarding message we send to a
        # user. We can use these objects to keep track of the progress each
        # user on each team has made getting through our onboarding tutorial.

        # First, we'll check to see if there's already messages our bot knows
        # of for the team id we've got.
        if self.messages.get(team_id):
            # Then we'll update the message dictionary with a key for the
            # user id we've recieved and a value of a new message object
            self.messages[team_id].update({user_id: message.Message()})
        else:
            # If there aren't any message for that team, we'll add a dictionary
            # of messages for that team id on our Bot's messages attribute
            # and we'll add the first message object to the dictionary with
            # the user's id as a key for easy access later.
            self.messages[team_id] = {user_id: message.Message()}
        message_obj = self.messages[team_id][user_id]
        # Then we'll set that message object's channel attribute to the DM
        # of the user we'll communicate with
        message_obj.channel = self.open_dm(user_id)
        # We'll use the message object's method to create the attachments that
        # we'll want to add to our Slack message. This method will also save
        # the attachments on the message object which we're accessing in the
        # API call below through the message object's `attachments` attribute.
        message_obj.create_attachments()
        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        timestamp = post_message["ts"]
        # We'll save the timestamp of the message we've just posted on the
        # message object which we'll use to update the message after a user
        # has completed an onboarding task.
        message_obj.timestamp = timestamp

    def update_emoji(self, team_id, user_id):
        """
        Update onboarding welcome message after recieving a "reaction_added"
        event from Slack. Update timestamp for welcome message.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # These updated attachments use markdown and emoji to mark the
        # onboarding task as complete
        completed_attachments = {"text": ":white_check_mark: "
                                         "~*Add an emoji reaction to this "
                                         "message*~ :thinking_face:",
                                 "color": "#439FE0"}
        # Grab the message object we want to update by team id and user id
        message_obj = self.messages[team_id].get(user_id)
        # Update the message's attachments by switching in incomplete
        # attachment with the completed one above.
        message_obj.emoji_attachment.update(completed_attachments)
        # Update the message in Slack
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]

    def update_pin(self, team_id, user_id):
        """
        Update onboarding welcome message after recieving a "pin_added"
        event from Slack. Update timestamp for welcome message.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # These updated attachments use markdown and emoji to mark the
        # onboarding task as complete
        completed_attachments = {"text": ":white_check_mark: "
                                         "~*Pin this message*~ "
                                         ":round_pushpin:",
                                 "color": "#439FE0"}
        # Grab the message object we want to update by team id and user id
        message_obj = self.messages[team_id].get(user_id)
        # Update the message's attachments by switching in incomplete
        # attachment with the completed one above.
        message_obj.pin_attachment.update(completed_attachments)
        # Update the message in Slack
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]

    def update_share(self, team_id, user_id):
        """
        Update onboarding welcome message after recieving a "message" event
        with an "is_share" attachment from Slack. Update timestamp for
        welcome message.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # These updated attachments use markdown and emoji to mark the
        # onboarding task as complete
        completed_attachments = {"text": ":white_check_mark: "
                                         "~*Share this Message*~ "
                                         ":mailbox_with_mail:",
                                 "color": "#439FE0"}
        # Grab the message object we want to update by team id and user id
        message_obj = self.messages[team_id].get(user_id)
        # Update the message's attachments by switching in incomplete
        # attachment with the completed one above.
        message_obj.share_attachment.update(completed_attachments)
        # Update the message in Slack
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]

    def post_message(self, channel, message_text):
        resp = self.client.api_call(
            "chat.postMessage",
            channel=channel,
            text=message_text
        )

        return resp

    def spotify_tracks(self, channel, message_text):
        self.spotify_work(channel, message_text, "track", conf.SPOTIFY_TRACK_PLAYLIST_ID, spotify_helper.extract_spotify_track_ids, spotify_helper.add_track_to_playlist)

    def spotify_albums(self, channel, message_text):
        self.spotify_work(channel, message_text, "album", conf.SPOTIFY_ALBUM_PLAYLIST_ID, spotify_helper.extract_spotify_album_ids, spotify_helper.add_album_to_playlist)

    def spotify_work(self, channel, message_text, extract_type, playlist_id, extract_method, add_method):
        spotify_ids = extract_method(message_text)
        if not spotify_ids:
            msg.warn("No spotify links found after parsing for {}s: {}".format(extract_type, message_text))
            return

        for spotify_id in spotify_ids:
            add_status, resp = add_method(spotify_id, playlist_id)
            if not add_status:
                self.post_message(channel, "Adding {} {} failed: {}".format(extract_type, spotify_id, resp.json()))
            else:
                self.post_message(channel, "Added {} {} to playlist!".format(extract_type, spotify_id))

    def spotify_discover(self, channel, message_text):
        self.spotify_work(channel, message_text, "discover", conf.SPOTIFY_DISCOVER_PLAYLIST_ID, spotify_helper.extract_spotify_discover_id, spotify_helper.add_discover_to_playlist)

    def handle_spotify(self, channel, message_text):
        if "!discover!" in message_text:
            self.spotify_discover(channel, message_text)
            return

        if spotify_helper.has_album_link(message_text):
            self.spotify_albums(channel, message_text)

        if spotify_helper.has_track_link(message_text):
            self.spotify_tracks(channel, message_text)

    def boom_roasted(self, channel, received_message_text):
        resp = self.post_message(channel, "BOOM ROASTED! ({})".format(received_message_text))

        msg.debug("Response: {}".format(resp))
