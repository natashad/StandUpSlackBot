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


standup_updates = "nobody has replied yet."


# SLACK CALLBACKS

@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
       return  _open_standup_dialog(payload)
    if payload.get('callback_id') == 'submit_standup':
       _save_standup_update(payload)
       #TODO: Send a successful message!
       return ""
    return "Sorry, I don't Understand"


def _save_standup_update(payload):
    # TODO: Save these updates better
    standup_result = ""
    if payload.get('type') == 'dialog_submission':
        for question, answer in payload.get('submission').items():
            standup_result = standup_result + question + ": " + (answer or '') + "\n"
            print(standup_result)
        global standup_updates
        standup_updates = standup_result

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
    # TODO: Make these questions configurable
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": "submit_standup",
            "title": "Today's Stand up Report",
            "submit_label": "Submit",
            "notify_on_cancel": False,
            "elements": [
                {
                    "type": "textarea",
                    "label": "Yesterday",
                    "hint": "What did you do yesterday?",
                    "name": "yesterday",
                    "optional": True
                },
                {
                    "type": "textarea",
                    "label": "Today",
                    "name": "today",
                    "hint": "What will you do today?",
                    "optional": True
                },
                {
                    "type": "textarea",
                    "label": "Blockers",
                    "name": "blockers",
                    "hint": "Is anything blocking you?",
                    "optional": True
                }
            ]
        }
    }
    _post_a_message(DIALOG_OPEN_ENDPOINT, dialog)

# SLACK EVENT API EVENT HANDLERS:

slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("message")
def message(event):
    event = event.get('event')
    if event.get('channel_type') != 'im' or not event.get('text'):
        return
    if event.get('text').lower() == 'stand up' or event.get('text').lower() == 'standup':
        _post_stand_up_message(event.get('channel'))
    if event.get('text').lower() == "print stand up":
        data = {'channel': event.get('channel'), 'text': standup_updates}
        _post_a_message(POST_MESSAGE_ENDPOINT, data)

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
    _post_a_message(POST_MESSAGE_ENDPOINT, data)


def _post_a_message(endpoint, data):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)
    }
    r = requests.post(endpoint, json=data, headers=headers)
    print(r.content)


if __name__ == "__main__":
    app.run(port=5000)
