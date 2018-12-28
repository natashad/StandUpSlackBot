import json
from unittest.mock import patch, MagicMock

from nose.tools import eq_
from tests.base_test import BaseTest
from standup_bot.slack_callbacks.standup_trigger import trigger_standup
from standup_bot.config import Config
from standup_bot.redis_client import RedisClient
from standup_bot.constants import (
    SKIP_MESSAGE,
    DIALOG_OPEN_ENDPOINT
)


class TestStandupTrigger(BaseTest):
    @patch('standup_bot.slack_callbacks.standup_trigger.post_standup_dialog_modal')
    def test_standup_trigger__skip_no_redis(self, post_standup_dialog_modal):
        payload = {
            'trigger_id': 'fake_trigger_id',
            'actions': [{
                'name': 'test_standup',
                'value': 'skip'
            }],
            'user': {
                'id': 'USER1TEST'
            }
        }
        result = trigger_standup(payload)
        post_standup_dialog_modal.assert_not_called()
        eq_(result, SKIP_MESSAGE)

    @patch('standup_bot.slack_callbacks.standup_trigger.post_standup_dialog_modal')
    def test_standup_trigger__skip__with_redis(self, post_standup_dialog_modal):
        payload = {
            'trigger_id': 'fake_trigger_id',
            'actions': [{
                'name': 'test_standup',
                'value': 'skip'
            }],
            'user': {
                'id': 'USER1TEST'
            }
        }
        redis_client = MagicMock()
        result = trigger_standup(payload, redis_client)
        post_standup_dialog_modal.assert_not_called()
        redis_client.save_standup_update_to_redis.assert_called_with(
            'test_standup',
            'USER1TEST',
            []
        )
        eq_(result, SKIP_MESSAGE)

    @patch('standup_bot.helpers.requests')
    @patch('standup_bot.redis_client.redis')
    def test_standup_trigger__open_dialog_with_redis_existing_cache(self, mock_redis_lib, mock_requests):
        payload = {
            'trigger_id': 'fake_trigger_id',
            'actions': [{
                'name': 'test_standup',
                'value': 'open_dialog'
            }],
            'user': {
                'id': 'USER1TEST'
            }
        }
        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps([
            ('A very long question that is over the character limit', 'User1 Answer2')
        ])
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient(self.test_configs)

        result = trigger_standup(payload, redis_client=redis_client, config=Config(self.test_configs))
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        elements = [
            {
                'type': 'textarea',
                'label': 'Question1',
                'hint': 'Question1',
                'name': 'Question1',
                'optional': True,
                'value': None
            },
            {
                'type': 'textarea',
                'label': 'A very long question ...',
                'hint': 'A very long question that is over the character limit',
                'name': 'A very long question that is over the character limit',
                'optional': True,
                'value': 'User1 Answer2'
            }
        ]
        mock_redis.get.assert_called_with('test_standup:USER1TEST')
        mock_requests.post.assert_called_with(
            DIALOG_OPEN_ENDPOINT,
            json={
                'trigger_id': 'fake_trigger_id',
                'dialog': {
                    'state': 'test_standup',
                    'callback_id': 'submit_standup',
                    'title': 'Today\'s Stand up Report',
                    'submit_label': 'Submit',
                    'notify_on_cancel': False,
                    'elements': elements
                }
            },
            headers=headers
        )
        eq_(result, "")

    @patch('standup_bot.helpers.requests')
    @patch('standup_bot.redis_client.redis')
    def test_standup_trigger__open_dialog_with_redis_no_cache(self, mock_redis_lib, mock_requests):
        payload = {
            'trigger_id': 'fake_trigger_id',
            'actions': [{
                'name': 'test_standup',
                'value': 'open_dialog'
            }],
            'user': {
                'id': 'USER1TEST'
            }
        }
        mock_redis = MagicMock()
        mock_redis.get.return_value = ''
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient(self.test_configs)

        result = trigger_standup(payload, redis_client=redis_client, config=Config(self.test_configs))
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        elements = [
            {
                'type': 'textarea',
                'label': 'Question1',
                'hint': 'Question1',
                'name': 'Question1',
                'optional': True,
                'value': None
            },
            {
                'type': 'textarea',
                'label': 'A very long question ...',
                'hint': 'A very long question that is over the character limit',
                'name': 'A very long question that is over the character limit',
                'optional': True,
                'value': None
            }
        ]
        mock_redis.get.assert_called_with('test_standup:USER1TEST')
        mock_requests.post.assert_called_with(
            DIALOG_OPEN_ENDPOINT,
            json={
                'trigger_id': 'fake_trigger_id',
                'dialog': {
                    'state': 'test_standup',
                    'callback_id': 'submit_standup',
                    'title': 'Today\'s Stand up Report',
                    'submit_label': 'Submit',
                    'notify_on_cancel': False,
                    'elements': elements
                }
            },
            headers=headers
        )
        eq_(result, "")

    @patch('standup_bot.helpers.requests')
    def test_standup_trigger_open_dialog_without_redis(self, mock_requests):
        payload = {
            'trigger_id': 'fake_trigger_id',
            'actions': [{
                'name': 'test_standup',
                'value': 'open_dialog'
            }],
            'user': {
                'id': 'USER1TEST'
            }
        }
        result = trigger_standup(payload, config=Config(self.test_configs))
        headers = {
            'content-type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer slackbot_auth_token'
        }
        elements = [
            {
                'type': 'textarea',
                'label': 'Question1',
                'hint': 'Question1',
                'name': 'Question1',
                'optional': True,
                'value': None
            },
            {
                'type': 'textarea',
                'label': 'A very long question ...',
                'hint': 'A very long question that is over the character limit',
                'name': 'A very long question that is over the character limit',
                'optional': True,
                'value': None
            }
        ]
        mock_requests.post.assert_called_with(
            DIALOG_OPEN_ENDPOINT,
            json={
                'trigger_id': 'fake_trigger_id',
                'dialog': {
                    'state': 'test_standup',
                    'callback_id': 'submit_standup',
                    'title': 'Today\'s Stand up Report',
                    'submit_label': 'Submit',
                    'notify_on_cancel': False,
                    'elements': elements
                }
            },
            headers=headers
        )
        eq_(result, "")
