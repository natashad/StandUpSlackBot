import requests

from standup_bot.config import Config
from standup_bot.constants import (
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT,
)
from standup_bot.redis_helper import (
    get_standup_report_for_team,
    save_standup_completed_state
)


class StandupBotHelper():
    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = Config()

    def get_standups_for_user(self, user_id):
        teams = []
        for standup in self.get_all_standups():
            team = self.get_standup_team(standup)
            if user_id in team:
                teams.append(standup)
        return teams

    def post_standup_prompt(self, channel, standup_name):
        attachments = [
            {
                'fallback': 'fallback',
                'callback_id': 'standup_trigger',
                'attachment_type': 'default',
                'actions': [
                    {
                        'name': standup_name,
                        'text': 'Open Dialog',
                        'type': 'button',
                        'value': 'open_dialog'
                    },
                    {
                        'name': standup_name,
                        'text': 'Skip',
                        'type': 'button',
                        'value': 'skip'
                    }
                ]
            }
        ]

        data = {
            'channel': channel,
            'text': 'Are you ready to start today\'s stand up? for *{}*'.format(standup_name),
            'attachments': attachments
        }
        return self.post_message_to_slack(data)

    def post_standup_report(self, standup_name, redis_client):
        if not redis_client:
            return

        channel = self.get_standup_channel(standup_name)
        standup_reports = get_standup_report_for_team(standup_name, redis_client)

        self.post_initial_standup_report_message(channel, len(standup_reports))

        if not standup_reports:
            return

        self.post_message_to_slack({
            'channel': channel,
            'text': "Standup for: *{}*".format(standup_name)
        })

        skipped_list = []

        for user in standup_reports:
            updates = standup_reports[user]
            username_info = "<@" + user + ">"

            attachments = self.get_standup_report_attachments(updates)

            if not attachments:
                skipped_list.append(username_info)
                continue

            data = {
                'channel': channel,
                'text': username_info,
                'attachments': attachments
            }
            self.post_message_to_slack(data)

        self.post_skipped_standup_message(channel, skipped_list)
        save_standup_completed_state(standup_name, redis_client)

    def post_message_to_slack(self, data, message_type='message'):
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer {}'.format(self.config.get('SLACKBOT_AUTH_TOKEN'))
        }
        if message_type == 'message':
            endpoint = POST_MESSAGE_ENDPOINT
        elif message_type == 'dialog':
            endpoint = DIALOG_OPEN_ENDPOINT
        return requests.post(endpoint, json=data, headers=headers)

    def get_standup_questions(self, standup):
        return self.get_standup_by_name(standup).get('questions')

    def get_standup_channel(self, standup):
        return self.get_standup_by_name(standup).get('channel')

    def get_standup_team(self, standup):
        return self.get_standup_by_name(standup).get('team')

    def get_standup_by_name(self, standup):
        return self.config.get('STANDUPS').get(standup)

    def get_all_standups(self):
        return self.config.get('STANDUPS')

    def get_standup_report_attachments(self, submission):
        attachments = []
        colors = ['#B2FFCC', '#66B2FF', '#FF6666']
        color_cursor = 0
        for question, answer in submission:
            if answer:
                attachments.append({
                    'title': question,
                    'text': answer,
                    'color': colors[color_cursor]
                })
            color_cursor = (color_cursor + 1) % len(colors)
        return attachments

    def post_initial_standup_report_message(self, channel, number_of_submissions):
        standup_complete_message = "<!here> Stand up is complete:\n"

        if number_of_submissions == 0:
            standup_complete_message = standup_complete_message + "I did not hear back from anyone."

        data = {
            'channel': channel,
            'text': standup_complete_message
        }
        self.post_message_to_slack(data)

    def post_skipped_standup_message(self, channel, skipped_list):
        if skipped_list:
            skipped_users = ", ".join(skipped_list)
            data = {
                'channel': channel,
                'text': "_{}_ skipped.".format(skipped_users)
            }
            self.post_message_to_slack(data)
