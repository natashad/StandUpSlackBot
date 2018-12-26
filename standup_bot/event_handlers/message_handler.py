from standup_bot.helpers import StandupBotHelper


def handle_event(event):
    event = event.get('event')

    helper = StandupBotHelper()

    if event.get('channel_type') != 'im' or not event.get('text'):
        return

    if event.get('text').lower() in ['standup', 'stand up']:
        for standup in helper.get_standups_for_user(event.get('user')):
            helper.post_standup_prompt(event.get('channel'), standup)
