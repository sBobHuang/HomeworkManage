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
        choices=[('计算机导论', '计算机导论'),
                 ('操作系统', '操作系统')
                 ],
        coerce=str
    )
    homeWork = SelectField(
        label='实验名称',
        choices=[('实验一', '实验一'),
                 ('实验二', '实验二')
                 ],
        coerce=str
    )
    file = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('提交')
