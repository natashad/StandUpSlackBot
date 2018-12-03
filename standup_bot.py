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
STANDUPS = json.loads(os.environ['STANDUPS'])

# This `app` represents your existing Flask app
app = Flask(__name__)


standup_updates = {}

#TODO Make this actually support multiple stand ups.
def _get_first_standup():
    return STANDUPS.get('6ix')

def _get_standup_questions():
    return _get_first_standup().get('questions')

# SLACK CALLBACKS

@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
        return  _open_standup_dialog(payload)
    if payload.get('callback_id') == 'submit_standup':
        _save_standup_update(payload)
        _post_a_message(POST_MESSAGE_ENDPOINT, {
            'channel': payload.get('channel').get('id'),
            'text': "Thank you :tada:"
        })
        return ""
    return "Sorry, I don't Understand"


def _save_standup_update(payload):
    user = payload.get('user').get('id')
    standup_result = []
    if payload.get('type') == 'dialog_submission':
        for question, answer in payload.get('submission').items():
            if answer:
                standup_result.append((question, answer))
        global standup_updates
        standup_updates[user] = standup_result

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
    elements = []
    count = 0
    for question in _get_standup_questions():
        truncated_question = question
        if len(truncated_question) > 24:
            truncated_question = question[0:21] + '...'
        elements.append({
            "type": "textarea",
            "label": truncated_question,
            "hint": question,
            "name": "question" + str(count),
            "optional": True
        })
        count = count + 1
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "callback_id": "submit_standup",
            "title": "Today's Stand up Report",
            "submit_label": "Submit",
            "notify_on_cancel": False,
            "elements": elements
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
        _post_stand_up_report(_get_first_standup().get('channel'))


def _post_stand_up_report(channel):
    standup_complete_message = "<!here> Stand up is complete:\n"
    if not len(standup_updates):
        standup_complete_message = standup_complete_message + "I did not hear back from anyone."
    data = {
        'channel': channel,
        'text': standup_complete_message
    }
    _post_a_message(POST_MESSAGE_ENDPOINT, data)

    for user, updates in standup_updates.items():
        username_info = "<@" + user + ">:"
        attachments = []
        for update in updates:
            attachments.append(
                {
                    'title': update[0],
                    'text': update[1]
                }
            )
        data = {
            'channel': channel,
            'text': username_info,
            'attachments': attachments
        }
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


if __name__ == "__main__":
    app.run(port=5000)
