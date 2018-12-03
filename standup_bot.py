from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from constants import (
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT
)
import json
import os
import requests
import urllib.parse

SLACK_SIGNING_SECRET = os.environ['SLACKBOT_SIGNING_SECRET']
SLACKBOT_AUTH_TOKEN = os.environ['SLACKBOT_AUTH_TOKEN']

# This `app` represents your existing Flask app
app = Flask(__name__)


# SLACK CALLBACKS

@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
       return  _open_standup_dialog(payload)
    return "Sorry, I don't Understand"


def _open_standup_dialog(payload):
    trigger_id = payload.get('trigger_id')
    action = payload.get('actions')[0]
    if action.get('value') == 'skip':
        return "Ok, I'll ask you again next stand up."
    elif action.get('value') == 'open_dialog':
        _post_standup_dialog(trigger_id)
        return ""
    else:
        return "Sorry, I don't understand"


def _post_standup_dialog(trigger_id):
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": "submit_standup",
            "title": "Today's Stand up Report",
            "submit_label": "Submit",
            "notify_on_cancel": False,
            "elements": [
                {
                    "type": "text",
                    "label": "Q1?",
                    "name": "yesterday"
                },
                {
                    "type": "text",
                    "label": "Q2?",
                    "name": "today"
                }
            ]
        }
    }
    headers = {'content-type' : 'application/json; charset=utf-8',
              'Authorization' : 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)}
    r = requests.post(DIALOG_OPEN_ENDPOINT, json=dialog, headers=headers)
    print(r.content)

# SLACK EVENT API EVENT HANDLERS:

slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("message")
def message(event):
    event = event.get('event')
    if event.get('channel_type') != 'im' or not event.get('text'):
        return
    if event.get('text').lower() == 'stand up' or event.get('text').lower() == 'standup':
        _post_stand_up_message(event.get('channel'))


def _post_stand_up_message(channel):
    attachments = [
            {
                'fallback' : 'fallback',
                'callback_id': 'standup_trigger',
                'attachment_type': 'default',
                'actions': [
                    {
                        'name': 'daily_standup',
                        'text': 'Open Dialog',
                        'type': 'button',
                        'value': 'open_dialog'
                    },
                    {
                        'name': 'daily_standup',
                        'text': 'Skip',
                        'type': 'button',
                        'value': 'skip'
                    }
                ]
            }
    ]

    data = {
        'channel': channel,
        'text': 'Are you ready to start your daily stand up?',
        'attachments': attachments
    }
    headers = {'content-type' : 'application/json; charset=utf-8',
              'Authorization' : 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)}
    r = requests.post(POST_MESSAGE_ENDPOINT, json=data, headers=headers)

if __name__ == "__main__":
    app.run(port=5000)
