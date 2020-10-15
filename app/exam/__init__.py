#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Blueprint

exam = Blueprint('exam', __name__)

from . import views
