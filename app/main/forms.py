#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, ValidationError


class UploadForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    studentID = StringField('学号', validators=[DataRequired()])
    course = SelectField(
        label='科目',
        choices=[('计算机导论', '计算机导论')
                 ],
        coerce=str
    )
    homeWork = SelectField(
        label='作业名称',
        choices=[('作业一', '作业一'),
                 ('作业二', '作业二')
                 ],
        coerce=str
    )
    file = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('提交')
