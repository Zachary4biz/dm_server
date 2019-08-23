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
YOLO_LOG_PATH = os.path.join(LOGDIR, "yolo_service.log")
CUTCUT_LOG_PATH = os.path.join(LOGDIR, "cutcut_profile.log")


class NLP:
    def __init__(self):
        pass
    tag_port = "http://newsprofile-keywords.internalapus.com/segment/tags.jsp"
    kw_port = "http://newsprofile-keywords.internalapus.com/segment/keywords.jsp"
