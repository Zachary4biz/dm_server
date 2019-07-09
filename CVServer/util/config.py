# author: zac
# create-time: 2019-07-09 14:44
# usage: - 
import os


def __get_dir(fn=__file__, level=0):
    return os.path.abspath(os.path.join(os.path.abspath(fn), "/".join([".."] * level)))


BASEPATH = __get_dir(__file__, 2)
LOGDIR = os.path.join(BASEPATH, "logs")
if not os.path.exists(LOGDIR):
    os.mkdir(LOGDIR)

AGE_LOG_PATH = os.path.join(LOGDIR, "age_service.log")
GENDER_LOG_PATH = os.path.join(LOGDIR, "gender_service.log")
NSFW_LOG_PATH = os.path.join(LOGDIR, "nsfw_service.log")

class NLP():
    tag_port = ""
    kw_port = ""
