from datetime import datetime, timedelta
from standup_bot.config import read_config
from standup_bot.constants import (
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT,
)

import json
import requests


config = read_config()


def get_standup_by_name(standup):
    return config.get('STANDUPS').get(standup)


def get_standup_questions(standup):
    return get_standup_by_name(standup).get('questions')


def get_standup_channel(standup):
    return get_standup_by_name(standup).get('channel')


def get_standup_team(standup):
    return get_standup_by_name(standup).get('team')


def get_all_standups():
    return config.get('STANDUPS')


def get_standups_for_user(user_id):
    teams = []
    for standup in get_all_standups():
        team = get_standup_team(standup)
        if user_id in team:
            teams.append(standup)
    return teams


def get_seconds_to_midnight():
    now = datetime.now()
    midnight = datetime(year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59)
    return (midnight - now).seconds


def get_standup_report_attachments(submission):
    attachments = []
    for question, answer in submission:
        if answer:
            attachments.append({
                'title': question,
                'text': answer
            })
    return attachments


def post_standup_prompt(channel, standup_name):
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
    return post_message_to_slack(data)


def post_standup_report(standup_name, redis_client):
    if not redis_client:
        return
    standup_complete_message = "<!here> Stand up is complete:\n"
    channel = get_standup_channel(standup_name)
    standup_redis_keys = redis_client.keys(standup_name + ":*")
    if not standup_redis_keys:
        standup_complete_message = standup_complete_message + "I did not hear back from anyone."
    data = {
        'channel': channel,
        'text': standup_complete_message
    }
    post_message_to_slack(data)

    if not standup_redis_keys:
        return

    post_message_to_slack({
        'channel': channel,
        'text': "Standup for: *{}*".format(standup_name)
    })
    for key in standup_redis_keys:
        key = key.decode('utf-8')
        user = key.split(':')[1]
        updates = json.loads(redis_client.get(key))
        username_info = "<@" + user + ">:"

        attachments = get_standup_report_attachments(updates)

        data = {
            'channel': channel,
            'text': username_info,
            'attachments': attachments
        }
        post_message_to_slack(data)

    redis_client.setex(
        "completed_standup:{}".format(standup_name),
        get_seconds_to_midnight(),
        'true'
    )


def post_message_to_slack(data, message_type='message'):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(config.get('SLACKBOT_AUTH_TOKEN'))
    }
    if message_type == 'message':
        endpoint = POST_MESSAGE_ENDPOINT
    elif message_type == 'dialog':
        endpoint = DIALOG_OPEN_ENDPOINT
    return requests.post(endpoint, json=data, headers=headers)
