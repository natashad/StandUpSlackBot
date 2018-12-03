# StandUpSlackBot
Stand Up Bot for Slack

## Getting Started / Installation:

### Assumption:
Assumes that you have created a Slack App with a bot with oauth scopes: `chat:write:bot`, `bot`, `commands`.
This bot should also have Interactive Components turned and pointing to `BASE_URL/slack/callbacks`
As well as Event Subscriptions for `message.im` pointing to the url `BASE_URL/slack/events`

1. Set up environment variables in a `.env` file:

For Development Purposes:
```
FLASK_APP='standup_bot'
FLASK_DEBUG=1

SLACKBOT_SIGNING_SECRET=`slackbot signing secret for your slack app`
SLAKCBOT_AUTH_TOKEN=`Slack bot auth token for your app`
```

Run the app locally:

`$ pipenv shell`

`$ flask run`

You will need to have something like ngrok set up to expose your local development environment to the interwebs while running this locally.
