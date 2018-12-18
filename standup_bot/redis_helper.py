import json

from standup_bot.helpers import (
    get_seconds_to_midnight
)
from standup_bot.constants import USER_MAPPING_PREFIX


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


def get_userid_from_username(user_name, redis_client):
    if not redis_client:
        return None
    user_id = redis_client.get(USER_MAPPING_PREFIX + user_name)
    return user_id.decode('utf-8')


def store_username_to_userid_mapping(user_id, user_name, redis_client):
    if not redis_client:
        return
    redis_client.set(USER_MAPPING_PREFIX + user_name, user_id)
