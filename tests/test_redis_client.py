from unittest.mock import MagicMock, patch

import json

from freezegun import freeze_time
from nose.tools import eq_
from tests.base_test import BaseTest
from standup_bot.redis_client import RedisClient


class TestRedisClient(BaseTest):
    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.redis_client.redis')
    def test_save_standup_update_to_redis__no_submissions(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        redis_client.save_standup_update_to_redis('my_standup', 'user2', [])
        mock_redis.setex.assert_called_with(
            'my_standup:user2',
            10 * 60 * 60,   # 10 hours until midnight given the frozen time
            '[]'
        )

    @freeze_time("2018-01-01 13:59:59")
    @patch('standup_bot.redis_client.redis')
    def test_save_standup_update_to_redis__missing_answer(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        standup_submission = {
            "Question 1": "Answer 1",
            "Question 2": "",
            "Question 3": "Answer 3"
        }.items()
        redis_client.save_standup_update_to_redis(
            'my_standup',
            'user2',
            standup_submission
        )
        mock_redis.setex.assert_called_with(
            'my_standup:user2',
            10 * 60 * 60,   # 10 hours until midnight given the frozen time
            json.dumps([
                ("Question 1", "Answer 1"),
                ("Question 3", "Answer 3")
            ])
        )

    @patch('standup_bot.redis_client.redis')
    def test_get_standup_report_for_user__ok(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        redis_client.get_standup_report_for_user('my_standup', 'user2')
        mock_redis.get.assert_called_with('my_standup:user2')

    @patch('standup_bot.redis_client.redis')
    def test_get_standup_report_for_team__no_keys(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        mock_redis.keys.return_value = []
        report = redis_client.get_standup_report_for_team('my_standup')
        eq_({}, report)

    @patch('standup_bot.redis_client.redis')
    def test_get_standup_report_for_team__ok(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        standup_results_1_json = json.dumps([
            ("Question 1", "Answer 1 for 1"),
            ("Question 3", "Answer 3 for 1")
        ])
        standup_results_2_json = json.dumps([
            ("Question 1", "Answer 1 for 2"),
            ("Question 2", "Answer 2 for 2")
        ])
        mock_redis.keys.return_value = [
            b'my_standup:user1',
            b'my_standup:user2'
        ]

        def side_effect(arg):
            if arg == 'my_standup:user1':
                return standup_results_1_json
            if arg == 'my_standup:user2':
                return standup_results_2_json
            return None
        mock_redis.get.side_effect = side_effect

        report = redis_client.get_standup_report_for_team('my_standup')
        expected = {
            'user1': json.loads(standup_results_1_json),
            'user2': json.loads(standup_results_2_json)
        }
        eq_(expected, report)

    @freeze_time("2018-01-01 11:59:59")
    @patch('standup_bot.redis_client.redis')
    def test_save_standup_completed_state__ok(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        redis_client.save_standup_completed_state('my_standup')
        mock_redis.setex.assert_called_with(
            'completed_standup:my_standup',
            12 * 60 * 60,
            'true'
        )

    @freeze_time("2018-01-01 11:59:59")
    @patch('standup_bot.redis_client.redis')
    def test_get_standup_completed_state__ok(self, mock_redis_lib):
        mock_redis = MagicMock()
        mock_redis_lib.from_url.return_value = mock_redis
        redis_client = RedisClient({'REDIS_URL': 'fake_url'})
        def side_effect(args):
            if args == 'completed_standup:my_standup':
                return 'true'
            return None
        mock_redis.get.side_effect = side_effect
        state = redis_client.get_standup_completed_state('my_standup')
        eq_('true', state)
