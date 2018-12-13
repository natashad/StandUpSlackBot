from standup_bot.helpers import (
    get_standups_for_user,
    post_standup_prompt
)


def handle_event(event):
    event = event.get('event')

    if event.get('channel_type') != 'im' or not event.get('text'):
        return

    if event.get('text').lower() in ['standup', 'stand up']:
        for standup in get_standups_for_user(event.get('user')):
            post_standup_prompt(event.get('channel'), standup)
