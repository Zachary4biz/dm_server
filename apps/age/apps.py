# author: zac
# create-time: 2019-10-08 21:26
# usage: - 
from django.apps import AppConfig
import os
from util.logger import Logger
from util.cv_util import CVUtil


nsfw_model = None
logger = Logger(loggername="Config", log2console=False, log2file=True, logfile="./age_apps.log").get_logger()
logger.info(">>> init at apps.py")
class Config(AppConfig):
    name = "age"

    def ready(self):
        global nsfw_model
        cv_util = CVUtil()
        base_path = os.path.abspath(os.path.dirname(__file__))
        logger.info(">>> load model ")
        nsfw_model = cv_util.load_model(prototxt_fp=base_path + "/model/nsfw_deploy.prototxt",
                                        caffemodel_fp=base_path + "/model/resnet_50_1by2_nsfw.caffemodel")

        print("nsfw's ready function done.")
