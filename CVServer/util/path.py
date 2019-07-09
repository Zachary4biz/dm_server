# author: zac
# create-time: 2019-07-09 14:44
# usage: - 
import os


def __get_dir(fn=__file__, level=0):
    return os.path.abspath(os.path.join(os.path.abspath(fn), "/".join([".."] * level)))


BASEPATH = __get_dir(__file__, 2)
LOGDIR = os.path.join(BASEPATH, "logs")

AGE_LOG_PATH = os.path.join(BASEPATH, "logs", "age_service.log")
GENDER_LOG_PATH = os.path.join(BASEPATH, "logs", "gender_service.log")
NSFW_LOG_PATH = os.path.join(BASEPATH, "logs", "nsfw_service.log")
