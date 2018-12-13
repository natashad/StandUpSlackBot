from standup_bot.helpers import (
    get_standup_channel,
    post_message_to_slack,
    get_seconds_to_midnight,
    get_standup_report_attachments
)

import json


def submit_standup(payload, redis_client, echo=False):
    standup_name = payload.get('state')
    if not redis_client:
        immediately_post_update(payload)
    else:
        user_channel = payload.get('channel').get('id')
        save_standup_update_to_redis(payload, redis_client)
        if redis_client.get('completed_standup:{}'.format(standup_name)):
            immediately_post_update(payload)
        if echo:
            immediately_post_update(payload, user_channel)

        standup_channel = get_standup_channel(standup_name)
        post_message_to_slack({
            'channel': user_channel,
            'text': "Stand up will be posted to *#{}* :tada:".format(standup_channel)
        })
        return ""
    return "Sorry, I don't Understand"


def immediately_post_update(payload, override_channel=None):
    standup_name = payload.get('state')
    channel = get_standup_channel(standup_name)
    user = payload.get('user').get('id')
    username_info = "<@" + user + ">:"

    attachments = get_standup_report_attachments(payload.get('submission').items())

    data = {
        'channel': override_channel or channel,
        'text': username_info,
        'attachments': attachments
    }
    post_message_to_slack(data)


def save_standup_update_to_redis(payload, redis_client):
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
    redis_client.setex(redis_key, get_seconds_to_midnight(), standup_result_str)
