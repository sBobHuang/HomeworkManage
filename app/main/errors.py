#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import main
from .api_exception import EmptyError


@main.app_errorhandler(404)
def page_not_found(e):
    return EmptyError(msg="404")


@main.app_errorhandler(500)
def internal_server_error(e):
    return EmptyError(msg="500")
