#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import os
import sqlite3
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    APP_ID = 'wxbb2e2f3094b20e73'
    APP_SECRET = '836a0d4cb8b0f0a0a45d2d69c1f5a6a2'
    AUTH_LOGIN_URL = 'https://api.weixin.qq.com/sns/jscode2session?appid={}' \
                     '&secret={}&js_code={}&grant_type=authorization_code '
    CURRENT_TERM = '204'
    CURRENT_PAY_TYPE = [0, 0, 0]
    SECRET_KEY = "BobHuang"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASK_MAIL_SUBJECT_PREFIX = '[Flask]'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN = "17858263110"
    FLASK_POSTS_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_USERNAME = "1161648480@qq.com"
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
