# author: zac
# create-time: 2019-09-16 10:40
# usage: - 
import os
path = os.path.join(os.path.abspath("."), "logs/localhost_{}.log")
CONFIG = {
    'profile': {
        "port": 8999,
        "host_logfile": path.format("profile")
    },
    'age': {
        "port": 8001,
        "host_logfile": path.format("age")
    },
    'gender': {
        "port": 8002,
        "host_logfile": path.format("gender")
    },
    'nsfw': {
        "port": 8003,
        "host_logfile": path.format("nsfw")
    },
    'obj': {
        "port": 8004,
        "host_logfile": path.format("obj")
    },
}
