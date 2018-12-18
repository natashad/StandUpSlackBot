import os
import json

EXPECTED_ENVIRONMENT_VARIABLES = [
    'SLACKBOT_SIGNING_SECRET',
    'SLACKBOT_AUTH_TOKEN',
    'STANDUPS',
    'REDIS_URL',  # optional
    'ECHO_STANDUP_REPORT'
]


def read_config():
    config = {}

    for env_var in EXPECTED_ENVIRONMENT_VARIABLES:
        value = os.environ[env_var]
        if value in ["0", "False", "false", "no"]:
            value = False
        config[env_var] = value

    config['STANDUPS'] = json.loads(config['STANDUPS'])

    return config
