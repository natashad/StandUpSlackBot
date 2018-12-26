import os
import json

EXPECTED_ENVIRONMENT_VARIABLES = [
    'SLACKBOT_SIGNING_SECRET',
    'SLACKBOT_AUTH_TOKEN',
    'STANDUPS',
    'REDIS_URL',  # optional
    'ECHO_STANDUP_REPORT'
]


class Config():
    def __init__(self, configs=None):
        self.config = {}

        config_variables = os.environ

        if configs:
            config_variables = configs

        for env_var in EXPECTED_ENVIRONMENT_VARIABLES:
            value = config_variables[env_var]
            if value in ["0", "False", "false", "no"]:
                value = False
            self.config[env_var] = value

        self.config['STANDUPS'] = json.loads(self.config['STANDUPS'])

    def get(self, key):
        return self.config.get(key)
