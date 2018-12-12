import sys
import calendar

from standup_bot.main import _post_stand_up_report
from datetime import datetime


WEEKENDS = [calendar.SATURDAY, calendar.SUNDAY]


def do_main():
    extra_ignore_days = sys.argv[2]
    ignore_days = WEEKENDS + extra_ignore_days
    if calendar.day_name[datetime.today().weekday()] in ignore_days:
        print("Do nothing, it's an ignore day")
        return
    standup_name = sys.argv[1]
    _post_stand_up_report(standup_name)


if __name__ == "__main__":
    do_main()
