#!/usr/bin/python
# -*- coding: utf-8 -*-
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
        choices=[('作业1', '作业1'),
                 ('作业2', '作业2')
                 ],
        coerce=str
    )
    file = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('提交')


class CalculatorForm(FlaskForm):
    form_title = '计算器'
    calculator_string = StringField('算式', validators=[DataRequired()])
    calculator_submit = SubmitField('提交查看结果')


class DownloadForm(FlaskForm):
    url = StringField('url', validators=[DataRequired(), Length(1, 200)])
    download_id = None
    submit = SubmitField('提交')
