import argparse
import calendar

from datetime import datetime


def parse_args():
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
    return args


def skip_job(args):
    ignore_days = [calendar.SATURDAY, calendar.SUNDAY]
    ignore_days = ignore_days + args.ignore_days
    return datetime.today().weekday() in ignore_days
