import redis

from standup_bot.helpers import post_standup_report
from standup_bot.config import read_config
from standup_bot.jobs.job_helper import (
    parse_args,
    skip_job
)


def do_main():
    args = parse_args()

    if skip_job(args):
        print("Skipping Job")
        return

    config = read_config()

    redis_client = None
    if config.get('REDIS_URL'):
        redis_client = redis.from_url(config.get('REDIS_URL'))

    post_standup_report(args.standup[0], redis_client)


if __name__ == "__main__":
    do_main()
