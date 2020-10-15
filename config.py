#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import os
import sqlite3
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    APP_ID = '****'
    APP_SECRET = '****'
    AUTH_LOGIN_URL = 'https://api.weixin.qq.com/sns/jscode2session?appid={}' \
                     '&secret={}&js_code={}&grant_type=authorization_code '
    CURRENT_TERM = '204'
    CURRENT_PAY_TYPE = [0, 0, 0]
    SECRET_KEY = "BobHuang"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASK_MAIL_SUBJECT_PREFIX = '[Flask]'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN = "****"
    FLASK_POSTS_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_USERNAME = "blog@bobhuang.xyz"
    MAIL_PASSWORD = "******"
    MAIL_PROT = 465
    MAIL_DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class TextingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TextingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def bakSqlite():
    conn = sqlite3.connect(os.path.join(basedir, 'data.sqlite'))
    with open('data.sqlite.bak', 'wb') as f:
        for line in conn.iterdump():
            data = line + '\n'
            data = data.encode("utf-8")
            f.write(data)
    print(datetime.utcnow(), '执行了定时备份任务')
