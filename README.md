# StandUpSlackBot
Stand Up Bot for Slack

## Getting Started / Installation:

### Assumption:
Assumes that you have created a Slack App with a bot with oauth scopes: `chat:write:bot`, `bot`, `commands`.
This bot should also have Interactive Components turned and pointing to `BASE_URL/slack/callbacks`
As well as Event Subscriptions for `message.im` pointing to the url `BASE_URL/slack/events`

1. Set up environment variables in a `.env` file:


```
SLACKBOT_SIGNING_SECRET=`slackbot signing secret for your slack app`
SLAKCBOT_AUTH_TOKEN=`Slack bot auth token for your app`
STANDUPS={
  'standup_name': {
    'team': ['team_member_slack_userid', ...],
    'channel': '#channel_name',
    'questions': ['Question 1', ['Question 2'], ...]
  }
} # This uses slack user_ids not username. This env variable should be minified json.
REDIS_URL=`redis_url` # Provided by default if running heroku-redis. Optional Field -- if Missing will post stand up update immediately.
ECHO_STANDUP_REPORT=1 # posts the standup report back to the user after they submit
```

### Run the app locally:

`$ pipenv shell`

`$ gunicorn standup_bot.main:app`

You will need to have something like ngrok set up to expose your local development environment to the interwebs while running this locally.


### Running the Jobs:

Triggering the stand up request message:
`$ python standup_bot/jobs/start_standup --standup "<standup_name>" --ignore_days 0 1`

Posting the stand up report:
`$ python standup_bot/jobs/post_standup --standup "<standup_name>" --ignore_days 0`

note: `ignore_days` specifies the days to skip stand ups. Multiple days can be passed in. It uses day number, starting with monday = 0. Weekends are ignored by default (5 - saturday, 6 - sunday)