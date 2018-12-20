import json
import requests

from standup_bot.jobs.base_job import BaseJob
from standup_bot.helpers import post_standup_prompt
from standup_bot.constants import IM_OPEN


class StartStandupJob(BaseJob):
    def do_job(self, config, standup_name):
        standup_team = config.get('STANDUPS').get(standup_name).get('team')

        for member in standup_team:
            print("sending to a member: {}".format(member))
            channel = self.open_IM_channel(
                config.get('SLACKBOT_AUTH_TOKEN'),
                member
            )
            if channel:
                post_standup_prompt(channel, standup_name)

    def open_IM_channel(self, auth_token, user):    # noqa pylint: disable=no-self-use
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer {}'.format(auth_token)
        }
        response = requests.post(IM_OPEN, json={'user': user}, headers=headers)
        response = json.loads(response.content)
        if response.get('ok'):
            channel = response.get('channel').get('id')
            return channel

        print("Response Error: {}".format(response))
        return None

if __name__ == "__main__":
    start_standup_job = StartStandupJob()
    start_standup_job.run_job()
