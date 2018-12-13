from standup_bot.helpers import (
    get_seconds_to_midnight
)

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
