from flask import Flask, request
from slackeventsapi import SlackEventAdapter
from standup_bot.config import read_config
from standup_bot.event_handlers.message_handler import handle_event as handle_message_event
from standup_bot.slack_callbacks.standup_trigger import trigger_standup
from standup_bot.slack_callbacks.standup_submit import submit_standup

import json
import redis


app = Flask(__name__)

config = read_config()

redis_client = None
if config.get('REDIS_URL'):
    redis_client = redis.from_url(config.get('REDIS_URL'))


# SLACK CALLBACKS
@app.route('/slack/callbacks', methods=['POST'])
def callbacks():
    payload = json.loads(request.form.get('payload'))
    if payload.get('callback_id') == 'standup_trigger':
        return trigger_standup(payload)
    if payload.get('callback_id') == 'submit_standup':
        return submit_standup(payload, redis_client, config.get('ECHO_STANDUP_REPORT'))


# SLACK EVENT API EVENT HANDLERS:
slack_events_adapter = SlackEventAdapter(
    config.get('SLACKBOT_SIGNING_SECRET'),
    "/slack/events",
    app
)


@slack_events_adapter.on("message")
def message(event):
    handle_message_event(event)
