import sys
import calendar
import argparse

from standup_bot.main import _post_stand_up_report
from datetime import datetime


WEEKENDS = [calendar.SATURDAY, calendar.SUNDAY]


def do_main():
    CLI = argparse.ArgumentParser()
    CLI.add_argument(
      "--standup",
      nargs=1,
      type=str
    )
    CLI.add_argument(
      "--ignore_days",
      nargs="*",
      type=int,
      default=[],
    )
    args = CLI.parse_args()

    print(args)

    if not args.standup:
        print("No standup provided")

    ignore_days = WEEKENDS + args.ignore_days

    if datetime.today().weekday() in ignore_days:
        print("Do nothing, it's an ignore day")
        return

    _post_stand_up_report(args.standup[0])


if __name__ == "__main__":
    do_main()
