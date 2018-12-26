import json as jsonlib
from unittest.mock import patch, call

from freezegun import freeze_time
from tests.base_test import BaseTest
from standup_bot.jobs.start_standup import StartStandupJob
from standup_bot.constants import (
    IM_OPEN,
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT
)


class TestStartStandup(BaseTest):
    @patch('standup_bot.jobs.start_standup.requests.post')
    def test_start_standup_job__no_ignore_days(self, mock_post):
        mock_post.side_effect = mock_post_side_effect
        mock_args = ["start_standup", "--standup", "test_standup"]
        with patch('sys.argv', mock_args):
            job = StartStandupJob(self.test_configs)
            job.run_job()
            headers = {
                'content-type': 'application/json; charset=utf-8',
                'Authorization': 'Bearer slackbot_auth_token'
            }
            attachments = [
                {
                    'fallback': 'fallback',
                    'callback_id': 'standup_trigger',
                    'attachment_type': 'default',
                    'actions': [
                        {
                            'name': 'test_standup',
                            'text': 'Open Dialog',
                            'type': 'button',
                            'value': 'open_dialog'
                        },
                        {
                            'name': 'test_standup',
                            'text': 'Skip',
                            'type': 'button',
                            'value': 'skip'
                        }
                    ]
                }
            ]
            post_message_standup_text = 'Are you ready to start today\'s stand up? for *test_standup*'

            call1 = call(
                IM_OPEN,
                json={'user': 'USER1TEST'},
                headers=headers
            )
            call2 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'IM_OPEN_CHANNEL',
                    'text': post_message_standup_text,
                    'attachments': attachments
                },
                headers=headers
            )
            call3 = call(
                IM_OPEN,
                json={'user': 'USER2TEST'},
                headers=headers
            )
            call4 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'IM_OPEN_CHANNEL',
                    'text': post_message_standup_text,
                    'attachments': attachments
                },
                headers=headers
            )
            mock_post.assert_has_calls([call1, call2, call3, call4])


    @patch('standup_bot.jobs.start_standup.StartStandupJob.do_job')
    def test_start_standup_job__no_standup_name(self, mock_do_job):
        mock_args = ["start_standup"]
        with patch('sys.argv', mock_args):
            job = StartStandupJob(self.test_configs)
            job.run_job()
            mock_do_job.assert_not_called()

    @freeze_time("2018-12-03 13:59:59") # A monday
    @patch('standup_bot.jobs.start_standup.StartStandupJob.do_job')
    def test_start_standup_job__ignore_day(self, mock_do_job):
        mock_args = ["start_standup", "--standup", "test_standup", "--ignore_days", "0"]
        with patch('sys.argv', mock_args):
            job = StartStandupJob(self.test_configs)
            job.run_job()
            mock_do_job.assert_not_called()

    @freeze_time("2018-12-03 13:59:59") # A monday
    @patch('standup_bot.jobs.start_standup.requests.post')
    def test_start_standup_job__ok(self, mock_post):
        mock_post.side_effect = mock_post_side_effect
        mock_args = ["start_standup", "--standup", "test_standup", "--ignore_days", "2"]
        with patch('sys.argv', mock_args):
            job = StartStandupJob(self.test_configs)
            job.run_job()
            headers = {
                'content-type': 'application/json; charset=utf-8',
                'Authorization': 'Bearer slackbot_auth_token'
            }
            attachments = [
                {
                    'fallback': 'fallback',
                    'callback_id': 'standup_trigger',
                    'attachment_type': 'default',
                    'actions': [
                        {
                            'name': 'test_standup',
                            'text': 'Open Dialog',
                            'type': 'button',
                            'value': 'open_dialog'
                        },
                        {
                            'name': 'test_standup',
                            'text': 'Skip',
                            'type': 'button',
                            'value': 'skip'
                        }
                    ]
                }
            ]
            post_message_standup_text = 'Are you ready to start today\'s stand up? for *test_standup*'

            call1 = call(
                IM_OPEN,
                json={'user': 'USER1TEST'},
                headers=headers
            )
            call2 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'IM_OPEN_CHANNEL',
                    'text': post_message_standup_text,
                    'attachments': attachments
                },
                headers=headers
            )
            call3 = call(
                IM_OPEN,
                json={'user': 'USER2TEST'},
                headers=headers
            )
            call4 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'IM_OPEN_CHANNEL',
                    'text': post_message_standup_text,
                    'attachments': attachments
                },
                headers=headers
            )
            mock_post.assert_has_calls([call1, call2, call3, call4])


def mock_post_side_effect(endpoint, json, headers):
    class MockResponse():
        def __init__(self, content):
            self.content = jsonlib.dumps(content)

    if endpoint == IM_OPEN:
        return MockResponse({'ok': True, 'channel': {'id': 'IM_OPEN_CHANNEL'}})
    if endpoint == POST_MESSAGE_ENDPOINT or endpoint == DIALOG_OPEN_ENDPOINT:
        return MockResponse({'ok': True})
