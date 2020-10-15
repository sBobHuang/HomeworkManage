# -*- coding: utf8 -*-
from werkzeug.exceptions import HTTPException
from flask import json


class ApiHttpException(HTTPException):
    message = "服务器繁忙"
    errcode = None
    data = []

    def __init__(self, msg=None, data=None, others=None):
        super(ApiHttpException, self).__init__(msg)
        if msg is not None:
            self.message = msg
        if data is not None:
            self.data = data
        self.others = others

    @property
    def generate_body(self):
        return {
            'code': self.errcode,
            'msg': self.message,
        }

    def get_body(self, environ=None):
        return json.dumps(self.generate_body)

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]


class ApiSuccess(ApiHttpException):
    @property
    def generate_body(self):
        t = {
            'code': self.errcode,
            'msg': self.message,
            'data':
                {
                    'list': []
                }
        }

        if self.data:
            t = dict(t, **{'data': {'list': self.data if isinstance(self.data, list) else [self.data]}})
        if self.others is not None and isinstance(self.others, dict):
            t['data'].update(self.others)
        return t


class ApiFailed(ApiHttpException):
    @property
    def generate_body(self):
        t = {
            'code': self.errcode,
            'msg': self.message,
            'data':
                {
                    'errlist': []
                }
        }
        if self.data:
            return dict(t, **{'data': {'errlist': self.data if isinstance(self.data, list) else [self.data]}})
        else:
            return t


class AuthSuccess(ApiSuccess):
    """ 授权 """
    code = 200
    errcode = 0


class UpdateSuccess(ApiSuccess):
    """ 更新 """
    code = 200
    errcode = 0


class RegisterSuccess(ApiSuccess):
    """ 添加 """
    code = 200
    errcode = 0


class DeleteSuccess(ApiSuccess):
    """ 删除 """
    code = 200
    message = u'删除成功'
    errcode = 0


class ViewSuccess(ApiSuccess):
    code = 200
    errcode = 0


class UploadSuccess(ApiSuccess):
    code = 200
    message = u'文件上传成功'
    errcode = 0


class AuthFailed(ApiFailed):
    code = 401
    message = u"授权失败"
    errcode = 4000


class NotFound(ApiFailed):
    code = 404
    message = u'资源不存在不存在'
    errcode = 4001


class Forbidden(ApiFailed):
    code = 403
    message = u'该页面禁止访问'
    errcode = 4002


class ServerError(ApiFailed):
    code = 500
    message = u'服务器内部错误'
    errcode = 4003


class InvalidToken(ApiFailed):
    code = 422
    message = u"访问令牌无效"
    errcode = 4004


class ExpirationFailed(ApiFailed):
    code = 422
    message = u"访问令牌过期"
    errcode = 4005


class RegisterFailed(ApiFailed):
    """ 注册失败 """
    code = 406
    message = u'注册失败'
    errcode = 4006


class FormError(ApiFailed):
    """ 表单格式错误 """
    code = 400
    errcode = 4007


class EmptyError(ApiFailed):
    code = 400
    message = u'提交的信息不完整'
    errcode = 4008


class DeleteFailed(ApiFailed):
    code = 400
    message = u'删除失败'
    errcode = 4009


class RepeatError(ApiFailed):
    code = 200
    message = u'该用户已经存在'
    errcode = 4010


class FormatError(ApiFailed):
    code = 200
    message = u'上传成功但文件格式不对,仅支持csv格式与xls文件'
    errcode = 4011


class SetSeatError(ApiSuccess):
    code = 200
    message = u'已经开课，暂无法选座，请联系相关课程老师解决。'
    errcode = 4012

