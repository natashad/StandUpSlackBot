from datetime import datetime

import calendar
import argparse

from standup_bot.config import read_config


class BaseJob():
    def run_job(self):
        args = self.parse_args()

        if self.skip_job(args):
            print("Skipping Job")
            return

        config = read_config()
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
