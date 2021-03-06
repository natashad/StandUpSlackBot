from standup_bot.jobs.base_job import BaseJob
from standup_bot.redis_client import RedisClient
from standup_bot.helpers import StandupBotHelper


class PostStandupJob(BaseJob):
    def do_job(self, config, standup_name):
        helper = StandupBotHelper(config)
        redis_client = None
        if config.get('REDIS_URL'):
            redis_client = RedisClient(config)

        helper.post_standup_report(standup_name, redis_client)


if __name__ == "__main__":
    post_standup_job = PostStandupJob()
    post_standup_job.run_job()
