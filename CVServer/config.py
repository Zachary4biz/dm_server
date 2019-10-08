# author: zac
# create-time: 2019-09-16 10:40
# usage: - 
import os
host_logfile = os.path.join(os.path.abspath("."), "logs/localhost_{}.log")
gunicorn_logfile = os.path.join(os.path.abspath("."), "logs/gunicorn_{}.log")


class Params:
    def __init__(self, port_, host_logfile_, gunicorn_logfile_):
        self.port = port_
        self.host_logfile = host_logfile_
        self.gunicorn_logfile = gunicorn_logfile_


CONFIG_NEW = {
    'age': Params(port_=9001,
                  host_logfile_=host_logfile.format("age"),
                  gunicorn_logfile_=gunicorn_logfile.format("age")),
    'gender': Params(port_=9002,
                     host_logfile_=host_logfile.format("gender"),
                     gunicorn_logfile_=gunicorn_logfile.format("gender")),
    'nsfw': Params(port_=9003,
                   host_logfile_=host_logfile.format("nsfw"),
                   gunicorn_logfile_=gunicorn_logfile.format("nsfw")),
    'obj': Params(port_=9004,
                  host_logfile_=host_logfile.format("obj"),
                  gunicorn_logfile_=gunicorn_logfile.format("obj")),
    'cutcut_profile': Params(port_=9000,
                             host_logfile_=host_logfile.format("cutcut_profile"),
                             gunicorn_logfile_=gunicorn_logfile.format("cutcut_profile")),
}

CONFIG = {
    'age': {
        "port": 8001,
        "host_logfile": host_logfile.format("age"),
        "gunicorn_logfile": gunicorn_logfile.format("age"),
    },
    'gender': {
        "port": 8002,
        "host_logfile": host_logfile.format("gender"),
        "gunicorn_logfile": gunicorn_logfile.format("gender"),
    },
    'nsfw': {
        "port": 8003,
        "host_logfile": host_logfile.format("nsfw"),
        "gunicorn_logfile": gunicorn_logfile.format("nsfw"),
    },
    'obj': {
        "port": 8004,
        "host_logfile": host_logfile.format("obj"),
        "gunicorn_logfile": gunicorn_logfile.format("obj"),
    },
    'cutcut_profile': {
        "port": 8000,
        "host_logfile": host_logfile.format("cutcut_profile"),
        "gunicorn_logfile": gunicorn_logfile.format("cutcut_profile"),
    },
}
