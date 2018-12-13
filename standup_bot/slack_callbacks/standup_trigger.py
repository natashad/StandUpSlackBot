from standup_bot.helpers import (
    post_message_to_slack,
    get_standup_questions,
    get_seconds_to_midnight
)
from standup_bot.redis_helper import (
    save_standup_update_to_redis,
    get_standup_report_for_user
)
from standup_bot.constants import DIALOG_LABEL_MAX_LENGTH

import json


def trigger_standup(payload, redis_client=None):
    trigger_id = payload.get('trigger_id')
    action = payload.get('actions')[0]
    standup_name = action.get('name')
    user_id = payload.get('user').get('id')

    if action.get('value') == 'skip':
        if redis_client:
            save_standup_update_to_redis(standup_name, user_id, [], redis_client)
        return "Ok, I'll ask you again next stand up."
    elif action.get('value') == 'open_dialog':
        post_standup_dialog_modal(trigger_id, user_id, standup_name, redis_client)
        return ""
    else:
        return "Sorry, I don't understand"


# Helpers
def post_standup_dialog_modal(trigger_id, user_id, standup_name, redis_client):
    elements = []
    report = []
    if redis_client:
        report = json.loads(get_standup_report_for_user(standup_name, user_id, redis_client))

    for question in get_standup_questions(standup_name):
        truncated_question = question
        if len(truncated_question) > DIALOG_LABEL_MAX_LENGTH:
            truncated_question = question[0:DIALOG_LABEL_MAX_LENGTH-3] + '...'

        default_value = None
        for submitted_question, submitted_answer in report:
            if submitted_question == question:
                default_value = submitted_answer
        elements.append({
            "type": "textarea",
            "label": truncated_question,
            "hint": question,
            "name": question,
            "optional": True,
            "value": default_value
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
    post_message_to_slack(dialog, message_type='dialog')