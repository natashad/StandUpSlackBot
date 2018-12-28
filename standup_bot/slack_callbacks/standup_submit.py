from standup_bot.constants import INVALID_INPUT_MESSAGE
from standup_bot.helpers import StandupBotHelper


def submit_standup(payload, redis_client=None, echo=False, config=None):
    standup_name = payload.get('state')
    user_channel = payload.get('channel').get('id')
    helper = StandupBotHelper(config)
    if not redis_client:
        if echo:
            immediately_post_update(payload, override_channel=user_channel, config=config)
        immediately_post_update(payload, config=config)
        return ""

    if payload.get('type') != 'dialog_submission':
        return INVALID_INPUT_MESSAGE
    userid = payload.get('user').get('id')
    submission = payload.get('submission').items()
    standup_name = payload.get('state')
    redis_client.save_standup_update_to_redis(standup_name, userid, submission)
    if redis_client.get_standup_completed_state(standup_name):
        immediately_post_update(payload, config=config)
    if echo:
        immediately_post_update(payload, override_channel=user_channel, config=config)

    standup_channel = helper.get_standup_channel(standup_name)
    helper.post_message_to_slack({
        'channel': user_channel,
        'text': "Stand up will be posted to *#{}* :tada:".format(standup_channel)
    })
    return ""


def immediately_post_update(payload, override_channel=None, config=None):
    standup_name = payload.get('state')
    helper = StandupBotHelper(config)
    channel = helper.get_standup_channel(standup_name)
    user = payload.get('user').get('id')
    username_info = "<@" + user + ">"

    attachments = helper.get_standup_report_attachments(payload.get('submission').items())

    data = {
        'channel': override_channel or channel,
        'text': username_info,
        'attachments': attachments
    }
    helper.post_message_to_slack(data)
