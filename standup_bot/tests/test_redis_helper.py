from unittest.mock import MagicMock

import json

from freezegun import freeze_time
from nose.tools import eq_
from standup_bot.tests.base_test import BaseTest
from standup_bot.redis_helper import (
    save_standup_update_to_redis,
    get_standup_report_for_user,
    get_standup_report_for_team,
    save_standup_completed_state,
    get_standup_completed_state
)


class TestRedisHelper(BaseTest):
    def setup(self):
        super().setup()
        self.mock_redis = MagicMock()   # noqa pylint: disable=attribute-defined-outside-init

    @freeze_time("2018-01-01 13:59:59")
    def test_save_standup_update_to_redis__no_submissions(self):
        save_standup_update_to_redis('my_standup', 'user2', [], self.mock_redis)
        self.mock_redis.setex.assert_called_with(
            'my_standup:user2',
            10 * 60 * 60,   # 10 hours until midnight given the frozen time
            '[]'
        )

    @freeze_time("2018-01-01 13:59:59")
    def test_save_standup_update_to_redis__missing_answer(self):
        standup_submission = {
            "Question 1": "Answer 1",
            "Question 2": "",
            "Question 3": "Answer 3"
        }.items()
        save_standup_update_to_redis(
            'my_standup',
            'user2',
            standup_submission,
            self.mock_redis
        )
        self.mock_redis.setex.assert_called_with(
            'my_standup:user2',
            10 * 60 * 60,   # 10 hours until midnight given the frozen time
            json.dumps([
                ("Question 1", "Answer 1"),
                ("Question 3", "Answer 3")
            ])
        )

    def test_get_standup_report_for_user__ok(self):
        get_standup_report_for_user('my_standup', 'user2', self.mock_redis)
        self.mock_redis.get.assert_called_with('my_standup:user2')

    def test_get_standup_report_for_team__no_keys(self):
        self.mock_redis.keys.return_value = []
        report = get_standup_report_for_team('my_standup', self.mock_redis)
        eq_({}, report)

    def test_get_standup_report_for_team__ok(self):
        standup_results_1_json = json.dumps([
            ("Question 1", "Answer 1 for 1"),
            ("Question 3", "Answer 3 for 1")
        ])
        standup_results_2_json = json.dumps([
            ("Question 1", "Answer 1 for 2"),
            ("Question 2", "Answer 2 for 2")
        ])
        self.mock_redis.keys.return_value = [
            b'my_standup:user1',
            b'my_standup:user2'
        ]

        def side_effect(arg):
            if arg == 'my_standup:user1':
                return standup_results_1_json
            if arg == 'my_standup:user2':
                return standup_results_2_json
            return None
        self.mock_redis.get.side_effect = side_effect

        report = get_standup_report_for_team('my_standup', self.mock_redis)
        expected = {
            'user1': json.loads(standup_results_1_json),
            'user2': json.loads(standup_results_2_json)
        }
        eq_(expected, report)

    @freeze_time("2018-01-01 11:59:59")
    def test_save_standup_completed_state__ok(self):
        save_standup_completed_state('my_standup', self.mock_redis)
        self.mock_redis.setex.assert_called_with(
            'completed_standup:my_standup',
            12 * 60 * 60,
            'true'
        )

    @freeze_time("2018-01-01 11:59:59")
    def test_get_standup_completed_state__ok(self):
        def side_effect(args):
            if args == 'completed_standup:my_standup':
                return 'true'
            return None
        self.mock_redis.get.side_effect = side_effect
        state = get_standup_completed_state('my_standup', self.mock_redis)
        eq_('true', state)
