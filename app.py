# -*- coding: utf-8 -*-
"""
A routing layer for the onboarding bot tutorial built using
[Slack's Events API](https://api.slack.com/events-api) in Python
"""
import json

from flask import Flask, request, make_response, render_template
from link import lnk

import bot
import conf


msg = lnk.msg

slack_bot = bot.Bot()
slack = slack_bot.client

app = Flask(__name__)


def _event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.

    Parameters
    ----------
    event_type : str
        type of event recieved from Slack
    slack_event : dict
        JSON response from a Slack reaction event
        https://api.slack.com/events/message

        sample event:
        {
           "api_app_id" : "AABF1PNQ6",
           "team_id" : "T053PNZAF",
           "event_time" : 1524249917,
           "authed_users" : [
              "UAA2KMCAV"
           ],
           "event" : {
              "type" : "message",
              "text" : "woop woop",
              "event_ts" : "1524249917.000693",
              "user" : "U10D3MFU2",
              "channel" : "CABF0AG4E",
              "ts" : "1524249917.000693"
           },
           "type" : "event_callback",
           "token" : "Cl5fltZBfYSQ2VjsyuJs8tr9",
           "event_id" : "EvAAJS58Q2"
        }


        Sample event from a bot (e.g. our own sent message):
        {
           "event" : {
              "type" : "message",
              "event_ts" : "1524255510.000240",
extra field --> "bot_id" : "BABM7FNSK",
extra field --> "subtype" : "bot_message",
              "text" : "BOOM ROASTED! (thanks bot)",
              "ts" : "1524255510.000240",
              "username" : "SpotifyBot",
              "channel" : "CABF0AG4E"
           },
           "event_time" : 1524255510,
           "team_id" : "T053PNZAF",
           "token" : "fWzlMgQxeNGjQFBDS897ZsyO",
           "event_id" : "EvAAHDUGH1",
           "api_app_id" : "AABM2R4NB",
           "type" : "event_callback",
           "authed_users" : [
              "UA9UPH532"
           ]
        }

    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error

    """
    msg.debug("Event type: {}, Event body: {}".format(event_type, slack_event))

    # currently ignore anything that's not just a regular message
    if not(event_type == "message" and 'subtype' not in slack_event['event']):
        return make_response("Not an event we care about", 200, {"X-Slack-No-Retry": 1})

    channel = slack_event['event']['channel']
    # Cannot lowercase for everything, bc track ID is case-sensitive
    message_text = slack_event['event']['text']

    if "fire it up!" in message_text.lower():
        slack_bot.boom_roasted(channel, message_text)
        return make_response("Message received", 200,)
    elif conf.SPOTIFY_BASE_URL in message_text:
        slack_bot.handle_spotify(channel, message_text)
        return make_response("Message received", 200,)
    else:
        return make_response("Not a message we care about", 200, {"X-Slack-No-Retry": 1})


@app.route("/status", methods=["GET"])
def status():
    return make_response("OK", 200,)


@app.route("/install", methods=["GET"])
def pre_install():
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = slack_bot.oauth["client_id"]
    scope = slack_bot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template("install.html", client_id=client_id, scope=scope)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    print("(DEBUG) Auth endpoint called")

    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    slack_bot.auth(code_arg)
    return render_template("thanks.html")


@app.route("/listening", methods=["GET", "POST"])
def hears():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    slack_event = json.loads(request.data)

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if slack_bot.verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], slack_bot.verification)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subscribed to
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
