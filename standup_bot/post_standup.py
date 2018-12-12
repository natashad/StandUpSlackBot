import sys

from standup_bot.main import _post_stand_up_report


def do_main():
    standup_name = sys.argv[1]
    _post_stand_up_report(standup_name)

if __name__ == "__main__":
    do_main()
