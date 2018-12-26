from datetime import datetime

import calendar
import argparse

from standup_bot.config import Config


class BaseJob():
    def __init__(self, configs=None):
        self.configs = configs

    def run_job(self):
        args = self.parse_args()

        if self.skip_job(args):
            print("Ignore day -- skipping job")
            return
        if not args.standup:
            print("No standup provided.")
            return

        config = Config(self.configs)
        self.do_job(config, args.standup[0])

    def do_job(self, config, standup_name):
        pass

    def parse_args(self):   # noqa pylint: disable=no-self-use
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

    def skip_job(self, args):   # noqa pylint: disable=no-self-use
        ignore_days = [calendar.SATURDAY, calendar.SUNDAY]
        ignore_days = ignore_days + args.ignore_days
        return datetime.today().weekday() in ignore_days
