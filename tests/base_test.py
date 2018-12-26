import json

from unittest.mock import patch

class BaseTest():
    def setup(self):
        standup_conf = {
            'test_standup': {
                'team': ['USER1TEST', 'USER2TEST'],
                'channel': 'testchannel',
                'questions': ['Question1', 'Question2', 'Question3']
            }

        }
        self.test_configs = {
            'SLACKBOT_SIGNING_SECRET': 'slackbot_signing_sekret',
            'SLACKBOT_AUTH_TOKEN': 'slackbot_auth_token',
            'STANDUPS': json.dumps(standup_conf),
            'REDIS_URL': '',
            'ECHO_STANDUP_REPORT': False
        }

    def teardown(self):
        pass
