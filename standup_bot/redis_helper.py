from datetime import datetime

import json


def save_standup_update_to_redis(standup_name, user_id, submission, redis_client):
    if not redis_client:
        return
    standup_result = []
    for question, answer in submission:
        if answer:
            standup_result.append((question, answer))

    redis_key = standup_name + ":" + user_id
    standup_result_str = json.dumps(standup_result)
    redis_client.setex(redis_key, get_seconds_to_midnight(), standup_result_str)


def get_standup_report_for_user(standup_name, user_id, redis_client):
    if not redis_client:
        return None
    redis_key = standup_name + ":" + user_id
    return redis_client.get(redis_key)


def get_standup_report_for_team(standup_name, redis_client):
    if not redis_client:
        return None

    standup_redis_keys = redis_client.keys(standup_name + ":*")
    standup_reports = {}

    for key in standup_redis_keys:
        key = key.decode('utf-8')
        user = key.split(':')[1]
        standup_submission = json.loads(redis_client.get(key))
        standup_reports[user] = standup_submission

    return standup_reports


def save_standup_completed_state(standup_name, redis_client):
    if not redis_client:
        return

    redis_client.setex(
        "completed_standup:{}".format(standup_name),
        get_seconds_to_midnight(),
        'true'
    )


def get_standup_completed_state(standup_name, redis_client):
    if not redis_client:
        return None

    return redis_client.get('completed_standup:{}'.format(standup_name))


def get_seconds_to_midnight():
    now = datetime.now()
    midnight = datetime(year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59)
    return (midnight - now).seconds
