import json as jsonlib
from unittest.mock import patch, call, MagicMock

from nose.tools import eq_
from freezegun import freeze_time
from tests.base_test import BaseTest
from standup_bot.jobs.post_standup import PostStandupJob
from standup_bot.constants import (
    IM_OPEN,
    POST_MESSAGE_ENDPOINT,
    DIALOG_OPEN_ENDPOINT
)


class TestPostStandup(BaseTest):

    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.helpers.requests.post')
    @patch('standup_bot.redis_client.redis')
    def test_post_standup_job__no_ignore_days(self, mock_redis_lib, mock_post):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        mock_redis.keys.return_value = [b'test_standup:USER1TEST', b'test_standup:USER2TEST']
        def redis_side_effect(key):
            if key == 'test_standup:USER1TEST':
                return jsonlib.dumps([
                    ("Question 1", "User1 Answer1"),
                    ("Question 2", "User1 Answer2")
                ])
            if key == 'test_standup:USER2TEST':
                return jsonlib.dumps([
                    ("Question 1", "User2 Answer1"),
                    ("Question 2", "User2 Answer2")
                ])
        mock_redis.get.side_effect = redis_side_effect
        mock_post.side_effect = mock_post_side_effect
        mock_args = ["post_standup", "--standup", "test_standup"]
        with patch('sys.argv', mock_args):
            job = PostStandupJob(self.test_configs)
            job.run_job()
            headers = {
                'content-type': 'application/json; charset=utf-8',
                'Authorization': 'Bearer slackbot_auth_token'
            }
            call1 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': "<!here> Stand up is complete:\n"
                },
                headers=headers
            )
            call2 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': 'Standup for: *test_standup*'
                },
                headers=headers
            )
            call3 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': '<@USER1TEST>',
                    'attachments': [
                        {
                            'title': 'Question 1',
                            'text': 'User1 Answer1',
                            'color': '#B2FFCC'
                        },
                        {
                            'title': 'Question 2',
                            'text': 'User1 Answer2',
                            'color': '#66B2FF'
                        }
                    ]
                },
                headers=headers
            )
            call4 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': '<@USER2TEST>',
                    'attachments': [
                        {
                            'title': 'Question 1',
                            'text': 'User2 Answer1',
                            'color': '#B2FFCC'
                        },
                        {
                            'title': 'Question 2',
                            'text': 'User2 Answer2',
                            'color': '#66B2FF'
                        }
                    ]
                },
                headers=headers
            )
            mock_post.assert_has_calls([call1, call2, call3, call4])
            eq_(4, mock_post.call_count)
            mock_redis.setex.assert_called_with(
                'completed_standup:test_standup',
                10 * 60 * 60,
                'true'
            )

    @freeze_time("2018-12-03 13:59:59")
    @patch('standup_bot.helpers.requests.post')
    @patch('standup_bot.redis_client.redis')
    def test_post_standup_job__no_participants(self, mock_redis_lib, mock_post):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        mock_redis.keys.return_value = []
        mock_post.side_effect = mock_post_side_effect
        mock_args = ["post_standup", "--standup", "test_standup", "--ignore_days", "2"]
        with patch('sys.argv', mock_args):
            job = PostStandupJob(self.test_configs)
            job.run_job()
            headers = {
                'content-type': 'application/json; charset=utf-8',
                'Authorization': 'Bearer slackbot_auth_token'
            }
            call1 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': "<!here> Stand up is complete:\nI did not hear back from anyone."
                },
                headers=headers
            )
            mock_post.assert_has_calls([call1])
            eq_(1, mock_post.call_count)

            mock_redis.setex.assert_called_with(
                'completed_standup:test_standup',
                10 * 60 * 60,
                'true'
            )

    @freeze_time("2018-12-03 13:59:59")
    @patch('standup_bot.helpers.requests.post')
    @patch('standup_bot.redis_client.redis')
    def test_post_standup_job__skipped_participants(self, mock_redis_lib, mock_post):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        mock_redis.keys.return_value = [b'test_standup:USER1TEST', b'test_standup:USER2TEST']
        def redis_side_effect(key):
            if key == 'test_standup:USER1TEST':
                return jsonlib.dumps([
                    ("Question 1", "User1 Answer1"),
                    ("Question 2", "User1 Answer2")
                ])
            if key == 'test_standup:USER2TEST':
                return jsonlib.dumps([])
        mock_redis.get.side_effect = redis_side_effect
        mock_post.side_effect = mock_post_side_effect
        mock_args = ["post_standup", "--standup", "test_standup"]
        with patch('sys.argv', mock_args):
            job = PostStandupJob(self.test_configs)
            job.run_job()
            headers = {
                'content-type': 'application/json; charset=utf-8',
                'Authorization': 'Bearer slackbot_auth_token'
            }
            call1 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': "<!here> Stand up is complete:\n"
                },
                headers=headers
            )
            call2 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': 'Standup for: *test_standup*'
                },
                headers=headers
            )
            call3 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': '<@USER1TEST>',
                    'attachments': [
                        {
                            'title': 'Question 1',
                            'text': 'User1 Answer1',
                            'color': '#B2FFCC'
                        },
                        {
                            'title': 'Question 2',
                            'text': 'User1 Answer2',
                            'color': '#66B2FF'
                        }
                    ]
                },
                headers=headers
            )
            call4 = call(
                POST_MESSAGE_ENDPOINT,
                json={
                    'channel': 'testchannel',
                    'text': '_<@USER2TEST>_ skipped.'
                },
                headers=headers
            )
            mock_post.assert_has_calls([call1, call2, call3, call4])
            eq_(4, mock_post.call_count)
            mock_redis.setex.assert_called_with(
                'completed_standup:test_standup',
                10 * 60 * 60,
                'true'
            )

    @patch('standup_bot.jobs.post_standup.PostStandupJob.do_job')
    def test_post_standup_job__no_standup_name(self, mock_do_job):
        mock_args = ["post_standup"]
        with patch('sys.argv', mock_args):
            job = PostStandupJob(self.test_configs)
            job.run_job()
            mock_do_job.assert_not_called()

    @freeze_time("2018-12-03 13:59:59") # A monday
    @patch('standup_bot.jobs.post_standup.PostStandupJob.do_job')
    def test_post_standup_job__ignore_day(self, mock_do_job):
        mock_args = ["post_standup", "--standup", "test_standup", "--ignore_days", "0"]
        with patch('sys.argv', mock_args):
            job = PostStandupJob(self.test_configs)
            job.run_job()
            mock_do_job.assert_not_called()


def mock_post_side_effect(endpoint, json, headers):
    class MockResponse():
        def __init__(self, content):
            self.content = jsonlib.dumps(content)

    if endpoint == POST_MESSAGE_ENDPOINT or endpoint == DIALOG_OPEN_ENDPOINT:
        return MockResponse({'ok': True})
