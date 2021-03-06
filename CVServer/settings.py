"""
Django settings for CVServer project.

Generated by 'django-admin startproject' using Django 1.11.21.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # server目录

sys.path.append(os.path.join(BASE_DIR))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vcv1!10!k*1^16!@5_)1g7xisfnefv9c+9*pa^%bnx*7e8_2p%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gunicorn',  # 正式部署
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CVServer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + "/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'CVServer.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

##############################
# 根据要起的服务加载算法模型
##############################
from config import CONFIG_NEW
SERVICE_NAME = os.environ['SERVICE_NAME']
ALGO_MODEL = {}
LOGGER = {}
for name, params in CONFIG_NEW.items():
    if SERVICE_NAME == "all":
        # 如果是一个server启了所有服务（同一端口不同路由），直接初始化所有模型和logger
        ALGO_MODEL.update({name: params.load_model()})
        LOGGER.update({name: params.logger})
    else:
        if name == SERVICE_NAME:
            # 如果这个server只启动了某个服务，则只加载该服务的模型和logger
            ALGO_MODEL.update({name: params.load_model()})
            LOGGER.update({name: params.logger})
        else:
            # 注意其他服务的也不能为空，因为在urls.py里使用了字典预先引入了各子服务的service模块
            # 如果为空会导致该service模块无法正常初始化（KeyError）
            ALGO_MODEL.update({name: None})
            LOGGER.update({name: None})
#
# if SERVICE_NAME == "all":
#     # 如果是一个server启了所有服务（同一端口不同路由），直接初始化所有模型和logger
#     for name, params in CONFIG_NEW.items():
#         ALGO_MODEL.update({name: params.load_model()})
#         LOGGER.update({name: params.logger})
# else:
#     # 如果这个server只启动了某个服务，则只加载该服务的模型和logger
#     ALGO_MODEL.update({SERVICE_NAME: CONFIG_NEW[SERVICE_NAME].load_model()})
#     LOGGER.update({SERVICE_NAME: CONFIG_NEW[SERVICE_NAME].logger})

