import sys
import os
import json
import requests

from standup_bot.helpers import post_standup_prompt
from standup_bot.constants import IM_OPEN
from standup_bot.jobs.job_helper import (
  parse_args,
  skip_job
)

SLACKBOT_AUTH_TOKEN = os.environ['SLACKBOT_AUTH_TOKEN']
STANDUPS = json.loads(os.environ['STANDUPS'])


def do_main():
    args = parse_args()

    if skip_job(args):
        print("Skipping Job")
        return

    standup_name = args.standup[0]
    standup = STANDUPS.get(standup_name)
    standup_team = standup.get('team')

    for member in standup_team:
        print("sending to a member: {}".format(member))
        channel = open_IM_channel(member)
        r = post_standup_prompt(channel, standup_name)


def open_IM_channel(user):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)
    }
    response = requests.post(IM_OPEN, json={'user': user}, headers=headers)
    response = json.loads(response.content)
    if response.get('ok'):
        channel = response.get('channel').get('id')
        return channel
    else:
        print("Response Error: {}".format(response))


if __name__ == "__main__":
    do_main()
