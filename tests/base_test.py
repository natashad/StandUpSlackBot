from unittest.mock import patch

class BaseTest():
    def setup(self):
        self.env_vars_patch = patch('standup_bot.config.get_environment_variables')   # noqa pylint: disable=attribute-defined-outside-init
        self.env_vars = self.env_vars_patch.start() # noqa pylint: disable=attribute-defined-outside-init
        self.env_vars.return_value = {
            'SLACKBOT_SIGNING_SECRET': 'slackbot_signing_sekret',
            'SLACKBOT_AUTH_TOKEN': 'slackbot_auth_token',
            'STANDUPS': {'test_standup': {}},
            'REDIS_URL': '',
            'ECHO_STANDUP_REPORT': 1
        }

    def teardown(self):
        self.env_vars_patch.stop()
