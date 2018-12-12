from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from standup_bot.constants import (
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT
)
from datetime import datetime, timedelta
import json
import os
import requests
import redis
import urllib.parse

SLACK_SIGNING_SECRET = os.environ['SLACKBOT_SIGNING_SECRET']
SLACKBOT_AUTH_TOKEN = os.environ['SLACKBOT_AUTH_TOKEN']
STANDUPS = json.loads(os.environ['STANDUPS'])
POST_REPORT_IMMEDIATELY = os.environ['POST_STANDUP_REPORT_IMMEDIATELY']
REDIS_URL = os.environ['REDIS_URL']
ECHO_STANDUP_REPORT = os.environ['ECHO_STANDUP_REPORT']

# This `app` represents your existing Flask app
app = Flask(__name__)

redis_client = None
if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL)


def _get_standup_questions(standup_name):
    return _get_standup_by_name(standup_name).get('questions')


def _get_standup_by_name(standup_name):
    return STANDUPS.get(standup_name)


# SLACK CALLBACKS
@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
        return _open_standup_dialog(payload)
    if payload.get('callback_id') == 'submit_standup':
        if POST_REPORT_IMMEDIATELY and POST_REPORT_IMMEDIATELY != "0":
            _immediately_post_update(payload)
        else:
            if redis_client:
                _save_standup_update_to_redis(payload)
        if ECHO_STANDUP_REPORT and ECHO_STANDUP_REPORT != "0":
            _immediately_post_update(payload, payload.get('channel').get('id'))

        standup_name = payload.get('state')
        post_to_channel = STANDUPS.get(standup_name).get('channel')
        _post_a_message(POST_MESSAGE_ENDPOINT, {
            'channel': payload.get('channel').get('id'),
            'text': "Stand up will be posted to *#{}* :tada:".format(post_to_channel)
        })
        return ""
    return "Sorry, I don't Understand"


def _immediately_post_update(payload, override_channel=None):
    standup_name = payload.get('state')
    channel = STANDUPS.get(standup_name).get('channel')
    user = payload.get('user').get('id')
    username_info = "<@" + user + ">:"
    attachments = []
    for question, answer in payload.get('submission').items():
        if answer:
            attachments.append({
                'title': question,
                'text': answer
            })
    data = {
        'channel': override_channel or channel,
        'text': username_info,
        'attachments': attachments
    }
    _post_a_message(POST_MESSAGE_ENDPOINT, data)


def _save_standup_update_to_redis(payload):
    if payload.get('type') != 'dialog_submission':
        return
    user = payload.get('user').get('id')
    standup_result = []
    for question, answer in payload.get('submission').items():
        if answer:
            standup_result.append((question, answer))
    standup_name = payload.get('state')
    redis_key = standup_name + ":" + user
    standup_result_str = json.dumps(standup_result)
    redis_client.setex(redis_key, _get_seconds_to_midnight(), standup_result_str)


def _get_seconds_to_midnight():
    now = datetime.now()
    midnight = datetime(year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59)
    return (midnight - now).seconds


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
    print("Received event")
    print("USER {}".format(event.get('event').get('user')))
    print("CHANNEL_TYPE : {}".format(event.get('event').get('channel_type')))
    event = event.get('event')
    if event.get('channel_type') != 'im' or not event.get('text'):
        return
    if event.get('text').lower() == 'stand up' or event.get('text').lower() == 'standup':
        print(_get_standups_for_user(event.get('user')))
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
    if not redis_client:
        return
    standup_complete_message = "<!here> Stand up is complete:\n"
    channel = STANDUPS.get(standup_name).get('channel')
    standup_redis_keys = redis_client.keys(standup_name + ":*")
    if not standup_redis_keys:
        standup_complete_message = standup_complete_message + "I did not hear back from anyone."
    data = {
        'channel': channel,
        'text': standup_complete_message
    }
    _post_a_message(POST_MESSAGE_ENDPOINT, data)

    if not standup_redis_keys:
        return

    _post_a_message(POST_MESSAGE_ENDPOINT, {'channel': channel, 'text': "Standup for: *{}*".format(standup_name)})
    for key in standup_redis_keys:
        key = key.decode('utf-8')
        user = key.split(':')[1]
        updates = json.loads(redis_client.get(key))
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
                'fallback': 'fallback',
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
