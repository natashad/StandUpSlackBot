import json as jsonlib
from unittest.mock import patch, call, MagicMock

from nose.tools import eq_
from freezegun import freeze_time
from tests.base_test import BaseTest
from standup_bot.slack_callbacks.standup_submit import submit_standup
from standup_bot.constants import POST_MESSAGE_ENDPOINT
from standup_bot.config import Config
from standup_bot.redis_client import RedisClient


class TestSubmitStandup(BaseTest):
    @patch('standup_bot.helpers.requests')
    def test_submit_standup__no_redis(self, mock_requests):
        payload = {
            'state': 'test_standup',
            'channel': {
                'id': 'User_1_test_channel'
            },
            'user': {
                'id': 'USER1TEST'
            },
            'submission': {
                'Question1': 'Answer1',
                'Question2': 'Answer2'
            },
            'type': 'dialog_submission'
        }
        result = submit_standup(payload, echo=True, config=Config(self.test_configs))
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        json1={
            'channel': 'User_1_test_channel',
            'text': '<@USER1TEST>',
            'attachments': [
                {
                    'title': 'Question1',
                    'text': 'Answer1',
                    'color': '#B2FFCC'
                },
                {
                    'title': 'Question2',
                    'text': 'Answer2',
                    'color': '#66B2FF'
                }
            ]
        }
        json2 = json1.copy()
        json2['channel'] = 'testchannel'

        call1 = call(
            POST_MESSAGE_ENDPOINT,
            json=json1,
            headers=headers
        )
        call2 = call(
            POST_MESSAGE_ENDPOINT,
            json=json2,
            headers=headers
        )
        mock_requests.post.assert_has_calls([call1, call2])
        eq_(2, mock_requests.post.call_count)
        eq_('', result)

    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.helpers.requests')
    @patch('standup_bot.redis_client.redis')
    def test_submit_standup__redis_standup_not_yet_posted(self, mock_redis_lib, mock_requests):
        payload = {
            'state': 'test_standup',
            'channel': {
                'id': 'User_1_test_channel'
            },
            'user': {
                'id': 'USER1TEST'
            },
            'submission': {
                'Question1': 'Answer1',
                'Question2': 'Answer2'
            },
            'type': 'dialog_submission'
        }
        mock_redis = MagicMock()
        # get standup_completed
        mock_redis.get.return_value = ''
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient(self.test_configs)
        result = submit_standup(payload, redis_client=redis_client, echo=True, config=Config(self.test_configs))
        mock_redis.setex.assert_called_with(
            'test_standup:USER1TEST',
            10 * 60 * 60,
            jsonlib.dumps([
                ('Question1', 'Answer1'),
                ('Question2', 'Answer2')
            ])
        )
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        json1={
            'channel': 'User_1_test_channel',
            'text': '<@USER1TEST>',
            'attachments': [
                {
                    'title': 'Question1',
                    'text': 'Answer1',
                    'color': '#B2FFCC'
                },
                {
                    'title': 'Question2',
                    'text': 'Answer2',
                    'color': '#66B2FF'
                }
            ]
        }

        call1 = call(
            POST_MESSAGE_ENDPOINT,
            json=json1,
            headers=headers
        )
        call2 = call(
            POST_MESSAGE_ENDPOINT,
            json={
                'channel': 'User_1_test_channel',
                'text': 'Stand up will be posted to *#testchannel* :tada:'
            },
            headers=headers
        )
        mock_requests.post.assert_has_calls([call1, call2])
        eq_(2, mock_requests.post.call_count)
        eq_('', result)

    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.helpers.requests')
    @patch('standup_bot.redis_client.redis')
    def test_submit_standup__redis_standup_completed(self, mock_redis_lib, mock_requests):
        payload = {
            'state': 'test_standup',
            'channel': {
                'id': 'User_1_test_channel'
            },
            'user': {
                'id': 'USER1TEST'
            },
            'submission': {
                'Question1': 'Answer1',
                'Question2': 'Answer2'
            },
            'type': 'dialog_submission'
        }
        mock_redis = MagicMock()
        # get standup_completed
        mock_redis.get.return_value = 'True'
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient(self.test_configs)
        result = submit_standup(payload, redis_client=redis_client, echo=True, config=Config(self.test_configs))
        mock_redis.setex.assert_called_with(
            'test_standup:USER1TEST',
            10 * 60 * 60,
            jsonlib.dumps([
                ('Question1', 'Answer1'),
                ('Question2', 'Answer2')
            ])
        )
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        json_echo={
            'channel': 'User_1_test_channel',
            'text': '<@USER1TEST>',
            'attachments': [
                {
                    'title': 'Question1',
                    'text': 'Answer1',
                    'color': '#B2FFCC'
                },
                {
                    'title': 'Question2',
                    'text': 'Answer2',
                    'color': '#66B2FF'
                }
            ]
        }
        json_channel = json_echo.copy()
        json_channel['channel'] = 'testchannel'

        call1 = call(
            POST_MESSAGE_ENDPOINT,
            json=json_channel,
            headers=headers
        )
        call2 = call(
            POST_MESSAGE_ENDPOINT,
            json=json_echo,
            headers=headers
        )
        call3 = call(
            POST_MESSAGE_ENDPOINT,
            json={
                'channel': 'User_1_test_channel',
                'text': 'Stand up will be posted to *#testchannel* :tada:'
            },
            headers=headers
        )
        mock_requests.post.assert_has_calls([call1, call2, call3])
        eq_(3, mock_requests.post.call_count)
        eq_('', result)

    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.helpers.requests')
    @patch('standup_bot.redis_client.redis')
    def test_submit_standup__redis_standup_completed__echo_off(self, mock_redis_lib, mock_requests):
        payload = {
            'state': 'test_standup',
            'channel': {
                'id': 'User_1_test_channel'
            },
            'user': {
                'id': 'USER1TEST'
            },
            'submission': {
                'Question1': 'Answer1',
                'Question2': 'Answer2'
            },
            'type': 'dialog_submission'
        }
        mock_redis = MagicMock()
        # get standup_completed
        mock_redis.get.return_value = 'True'
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient(self.test_configs)
        result = submit_standup(payload, redis_client=redis_client, echo=False, config=Config(self.test_configs))
        mock_redis.setex.assert_called_with(
            'test_standup:USER1TEST',
            10 * 60 * 60,
            jsonlib.dumps([
                ('Question1', 'Answer1'),
                ('Question2', 'Answer2')
            ])
        )
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        json_channel={
            'channel': 'testchannel',
            'text': '<@USER1TEST>',
            'attachments': [
                {
                    'title': 'Question1',
                    'text': 'Answer1',
                    'color': '#B2FFCC'
                },
                {
                    'title': 'Question2',
                    'text': 'Answer2',
                    'color': '#66B2FF'
                }
            ]
        }

        call1 = call(
            POST_MESSAGE_ENDPOINT,
            json=json_channel,
            headers=headers
        )
        call2 = call(
            POST_MESSAGE_ENDPOINT,
            json={
                'channel': 'User_1_test_channel',
                'text': 'Stand up will be posted to *#testchannel* :tada:'
            },
            headers=headers
        )
        mock_requests.post.assert_has_calls([call1, call2])
        eq_(2, mock_requests.post.call_count)
        eq_('', result)
