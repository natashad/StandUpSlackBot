from standup_bot.helpers import (
    get_standup_channel,
    post_message_to_slack,
    get_standup_report_attachments
)

from standup_bot.redis_helper import (
    save_standup_update_to_redis
)

import json


def submit_standup(payload, redis_client, echo=False):
    standup_name = payload.get('state')
    if not redis_client:
        immediately_post_update(payload)
    else:
        user_channel = payload.get('channel').get('id')
        if payload.get('type') != 'dialog_submission':
            return
        userid = payload.get('user').get('id')
        submission = payload.get('submission').items()
        standup_name = payload.get('state')
        save_standup_update_to_redis(standup_name, userid, submission, redis_client)
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
    username_info = "<@" + user + ">"

    attachments = get_standup_report_attachments(payload.get('submission').items())

    data = {
        'channel': override_channel or channel,
        'text': username_info,
        'attachments': attachments
    }
    post_message_to_slack(data)
