from datetime import datetime

import argparse
import calendar
import json
import requests

from standup_bot.config import read_config
from standup_bot.constants import USERS_LIST
from standup_bot.redis_helper import (
    store_username_to_userid_mapping,
    get_userid_from_username
)


config = read_config()


def parse_args():
    CLI = argparse.ArgumentParser()
    CLI.add_argument(
      "--standup",
      nargs=1,
      type=str
    )
    CLI.add_argument(
      "--ignore_days",
      nargs="*",
      type=int,
      default=[],
    )
    args = CLI.parse_args()
    return args


def skip_job(args):
    ignore_days = [calendar.SATURDAY, calendar.SUNDAY]
    ignore_days = ignore_days + args.ignore_days
    return datetime.today().weekday() in ignore_days


def map_userid_to_usernames_and_save(usernames, redis_client):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(config.get('SLACKBOT_AUTH_TOKEN'))
    }
    mapping = {}

    response = requests.get(USERS_LIST, headers=headers)
    response = json.loads(response.content)
    if not response.get('ok'):
        return {}

    members = response.get('members')
    for member in members:
        uname = member.get('profile').get('display_name_normalized')
        if uname in usernames:
            userid = member.get('id')
            mapping[uname] = userid
            if redis_client:
                store_username_to_userid_mapping(userid, uname, redis_client)
    return mapping


def get_standup_team_with_userids(standup_name, redis_client):
    standups = config.get('STANDUPS')
    standup = standups.get(standup_name)
    standup_team = standup.get('team')
    if not config.get('USE_USERNAMES_IN_TEAM'):
        return standup_team

    team_userids = []
    missing_usernames = standup_team
    if redis_client:
        missing_usernames = []
        for member in standup_team:
            userid = get_userid_from_username(member, redis_client)
            if not userid:
                missing_usernames.append(member)
            else:
                team_userids.append(userid)

    missing_userids = map_userid_to_usernames_and_save(missing_usernames, redis_client)
    missing_userids = list(missing_userids.values())
    return team_userids + missing_userids
