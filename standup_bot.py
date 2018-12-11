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
POST_REPORT_IMMEDIATELY = (os.environ['POST_STANDUP_REPORT_IMMEDIATELY'])

# This `app` represents your existing Flask app
app = Flask(__name__)


standup_updates = {}

def _get_standup_questions(standup_name):
    return _get_standup_by_name(standup_name).get('questions')


def _get_standup_by_name(standup_name):
    return STANDUPS.get(standup_name)


# SLACK CALLBACKS

@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
        return  _open_standup_dialog(payload)
    if payload.get('callback_id') == 'submit_standup':
        if POST_REPORT_IMMEDIATELY:
            _immediately_post_update(payload)
        else:
            _save_standup_update(payload)

        _post_a_message(POST_MESSAGE_ENDPOINT, {
            'channel': payload.get('channel').get('id'),
            'text': "Stand up submitted :tada:"

        })
        return ""
    return "Sorry, I don't Understand"


def _immediately_post_update(payload):
    standup_name = payload.get('state')
    channel = STANDUPS.get(standup_name).get('channel')
    user = payload.get('user').get('id')
    username_info = "<@" + user + ">:"
    attachments = []
    for question, answer in payload.get('submission').items():
        attachments.append({
            'title': question,
            'text': answer
        })
    data = {
        'channel': channel,
        'text': username_info,
        'attachments': attachments
    }
    _post_a_message(POST_MESSAGE_ENDPOINT, data)

def _save_standup_update(payload):
    if payload.get('type') != 'dialog_submission':
        return
    user = payload.get('user').get('id')
    standup_result = []
    for question, answer in payload.get('submission').items():
        if answer:
            standup_result.append((question, answer))
    standup_name = payload.get('state')
    global standup_updates
    if not standup_updates.get(standup_name):
        standup_updates[standup_name] = {}
    standup_updates[standup_name][user] = standup_result

def _open_standup_dialog(payload):
    trigger_id = payload.get('trigger_id')
    action = payload.get('actions')[0]
    standup_name = action.get('name')
    if action.get('value') == 'skip':
        return "Ok, I'll ask you again next stand up."
    elif action.get('value') == 'open_dialog':
        _post_standup_dialog(trigger_id, standup_name)
        return ""
    else:
        return "Sorry, I don't understand"


def _post_standup_dialog(trigger_id, standup_name):
    elements = []
    for question in _get_standup_questions(standup_name):
        truncated_question = question
        if len(truncated_question) > 24:
            truncated_question = question[0:21] + '...'
        elements.append({
            "type": "textarea",
            "label": truncated_question,
            "hint": question,
            "name": question,
            "optional": True
        })
    dialog = {
        "trigger_id": trigger_id,
        "dialog": {
            "state": standup_name,
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
        for standup in _get_standups_for_user(event.get('user')):
            _post_stand_up_message(event.get('channel'), standup)

def _get_standups_for_user(userid):
    teams = []
    for standup in STANDUPS:
        standup_config = STANDUPS.get(standup)
        team = standup_config.get('team')
        if userid in team:
            teams.append(standup)
    return teams

def _post_stand_up_report(standup_name):
    standup_complete_message = "<!here> Stand up is complete:\n"
    channel = STANDUPS.get(standup_name).get('channel')
    if not standup_updates.get(standup_name):
        standup_complete_message = standup_complete_message + "I did not hear back from anyone."
    data = {
        'channel': channel,
        'text': standup_complete_message
    }
    _post_a_message(POST_MESSAGE_ENDPOINT, data)

    if not standup_updates.get(standup_name):
        return

    _post_a_message(POST_MESSAGE_ENDPOINT, {'channel': channel, 'text': "Standup for: " + standup_name})
    for user, updates in standup_updates.get(standup_name).items():
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


def _post_stand_up_message(channel, standup_name):
    attachments = [
            {
                'fallback' : 'fallback',
                'callback_id': 'standup_trigger',
                'attachment_type': 'default',
                'actions': [
                    {
                        'name': standup_name,
                        'text': 'Open Dialog',
                        'type': 'button',
                        'value': 'open_dialog'
                    },
                    {
                        'name': standup_name,
                        'text': 'Skip',
                        'type': 'button',
                        'value': 'skip'
                    }
                ]
            }
    ]

    data = {
        'channel': channel,
        'text': 'Are you ready to start today\'s stand up? for *{}*'.format(standup_name),
        'attachments': attachments
    }
    return _post_a_message(POST_MESSAGE_ENDPOINT, data)


def _post_a_message(endpoint, data):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)
    }
    res = requests.post(endpoint, json=data, headers=headers)
    return res

if __name__ == "__main__":
    app.run(port=5000)
