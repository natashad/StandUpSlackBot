import sys
import os
import json
import requests

from standup_bot import _post_stand_up_message
from constants import IM_OPEN

SLACKBOT_AUTH_TOKEN = os.environ['SLACKBOT_AUTH_TOKEN']
STANDUPS = json.loads(os.environ['STANDUPS'])

def do_main():
    standup_name = sys.argv[1]
    standup = STANDUPS.get(standup_name)
    print(standup)
    standup_team = standup.get('team')
    print(str(standup_team) + " __ TEAM")

    for member in standup_team:
        print("sending to a member: {}".format(member))
        channel = open_IM_channel(member)
        r = _post_stand_up_message(channel, standup_name)

def open_IM_channel(user):
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'Authorization': 'Bearer {}'.format(SLACKBOT_AUTH_TOKEN)
    }
    response = requests.post(IM_OPEN, json={'user': user}, headers=headers)
    response = json.loads(response.content)
    if response.get('ok') == True:
        channel = response.get('channel').get('id')
        return channel
    else:
        print("Response Error: {}".format(response))

if __name__ == "__main__":
    do_main()

